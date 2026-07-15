"""
pallet_optimizer.py

WHAT THIS FILE DOES (small why):
Takes the carton dimensions from Module 2 and figures out how many cartons
fit on a shipping pallet -- both how many fit on one layer (the floor of the
pallet) and how many layers can be stacked on top of each other.

WHY THIS MATTERS (big why):
Step 3 of the cascade:
  Carton -> Optimize Pallet -> Optimize Container -> ...
A pallet is a flat wooden base with a footprint (like a rug) and a max safe
stack height. This is a 2D packing problem for the footprint (like arranging
rectangular tiles on a floor) combined with simple division for how many
layers stack vertically (like stacking boxes on a table until you hit the
ceiling).
"""

from dataclasses import dataclass

from app.services.carton_optimizer import CartonResult


# Standard pallet footprints (cm) - documented assumption in README
PALLET_TYPES = {
    "EURO": {"length_cm": 120, "width_cm": 80},
    "STANDARD": {"length_cm": 121.9, "width_cm": 101.6},  # 48x40 inch pallet
}

MAX_STACK_HEIGHT_CM = 180  # safe stacking height for handling/forklift, documented assumption
MAX_PALLET_WEIGHT_KG = 1000  # typical safe pallet weight limit, documented assumption


@dataclass
class PalletResult:
    pallet_type: str
    cartons_per_layer: int
    layers: int
    cartons_per_pallet: int
    pallet_height_cm: float
    total_weight_kg: float


def _cartons_per_layer(pallet_dims: tuple[float, float],
                        carton_footprint: tuple[float, float]) -> int:
    """
    2D packing: like laying rectangular tiles on a rectangular floor.
    Try both orientations (carton rotated 90 degrees) and take whichever
    lets more cartons fit on the pallet footprint.
    """
    pl, pw = pallet_dims
    cl, cw = carton_footprint

    # orientation 1: carton length along pallet length
    n1 = int(pl // cl) * int(pw // cw)
    # orientation 2: carton rotated 90 degrees
    n2 = int(pl // cw) * int(pw // cl)

    return max(n1, n2)


def optimize_pallet(carton: CartonResult, pallet_type: str = "EURO") -> PalletResult:
    """
    Picks the given pallet type, computes cartons per layer via 2D packing,
    computes how many layers fit under the max safe stack height, and
    multiplies them together for total cartons per pallet.

    Then checks the resulting total weight against a safe pallet weight limit
    and caps layers down if needed (a real forklift/rack has a max load).
    """
    if pallet_type not in PALLET_TYPES:
        raise ValueError(f"Unknown pallet_type: {pallet_type}")

    pallet_dims = (PALLET_TYPES[pallet_type]["length_cm"], PALLET_TYPES[pallet_type]["width_cm"])
    carton_footprint = (carton.carton_length_cm, carton.carton_width_cm)

    per_layer = _cartons_per_layer(pallet_dims, carton_footprint)
    if per_layer == 0:
        raise ValueError("Carton footprint is larger than the pallet itself")

    max_layers_by_height = int(MAX_STACK_HEIGHT_CM // carton.carton_height_cm)

    # start from height-based layer limit, then reduce further if weight limit is hit
    layers = max(max_layers_by_height, 1)
    while layers > 1:
        total_weight = per_layer * layers * carton.carton_weight_kg
        if total_weight <= MAX_PALLET_WEIGHT_KG:
            break
        layers -= 1

    cartons_per_pallet = per_layer * layers
    total_weight_kg = round(cartons_per_pallet * carton.carton_weight_kg, 2)
    pallet_height_cm = round(layers * carton.carton_height_cm, 2)

    return PalletResult(
        pallet_type=pallet_type,
        cartons_per_layer=per_layer,
        layers=layers,
        cartons_per_pallet=cartons_per_pallet,
        pallet_height_cm=pallet_height_cm,
        total_weight_kg=total_weight_kg,
    )
