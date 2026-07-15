"""
container_optimizer.py

WHAT THIS FILE DOES (small why):
Takes the pallet configuration from Module 3 and figures out, for each of the
3 standard shipping container types (20GP, 40GP, 40HC):
  - how many pallets fit inside
  - how many containers are needed for the total shipment quantity
  - how much of the container's space is actually used (utilization)
  - how much it costs in freight

Then it picks whichever container type gives the lowest TOTAL freight cost
for this specific shipment.

WHY THIS MATTERS (big why):
Final step of the physical cascade:
  Pallet -> Optimize Container -> Compare Multiple Scenarios -> Recommend Lowest Cost
Tea is light for its size (low density), so a shipment often runs out of
SPACE in a container long before it runs out of allowed WEIGHT. That means
the "best" container isn't always the biggest one -- it's whichever one wastes
the least space for THIS shipment's specific volume-to-weight ratio. This is
the module where that trade-off actually gets calculated instead of assumed.
"""

from dataclasses import dataclass
import math

from app.services.pallet_optimizer import PalletResult
from app.services.carton_optimizer import CartonResult


# Internal usable dimensions (cm) and specs for standard containers.
# These are standardized industry dimensions (ISO container specs).
CONTAINER_TYPES = {
    "20GP": {"length_cm": 589, "width_cm": 235, "height_cm": 239, "max_weight_kg": 28200},
    "40GP": {"length_cm": 1203, "width_cm": 235, "height_cm": 239, "max_weight_kg": 26500},
    "40HC": {"length_cm": 1203, "width_cm": 235, "height_cm": 269, "max_weight_kg": 26000},
}

# Simplified average freight cost per container by type (USD) - a real system
# would pull live rates from a freight API; this is a documented assumption
# so the cost comparison logic is demonstrable and explainable.
FREIGHT_COST_USD = {
    "20GP": 1800,
    "40GP": 2600,
    "40HC": 2800,
}

MAX_PALLET_STACK_LAYERS = 1  # most containers only safely fit 1 layer of pallets high; documented assumption


@dataclass
class ContainerResult:
    container_type: str
    pallets_per_container: int
    containers_required: int
    total_units_shipped: int
    container_utilization: float   # 0-1, fraction of container volume used
    empty_space_pct: float
    freight_cost_usd: float


def _pallets_per_container(container_dims: tuple[float, float],
                            pallet_footprint: tuple[float, float]) -> int:
    """
    Same 2D packing idea as Module 3 (cartons on a pallet), just one level up:
    now we're fitting pallets onto the container floor. Try both orientations.
    """
    cl, cw = container_dims
    pl, pw = pallet_footprint

    n1 = int(cl // pl) * int(cw // pw)
    n2 = int(cl // pw) * int(cw // pl)

    return max(n1, n2) * MAX_PALLET_STACK_LAYERS


def evaluate_all_containers(pallet: PalletResult, carton: CartonResult,
                             total_units: int) -> list[ContainerResult]:
    """
    Runs the comparison across all 3 container types and returns all results
    (not just the best one) so Module 6's "Compare: 20GP / 40GP / 40HC" table
    in the PDF is fully populated with real numbers, not guesses.

    NOTE: "total_units" here means individual tea packages (pouches) -- the
    same unit the user enters as "Shipment Quantity" in Module 2 of the app.
    We convert cartons -> pouches explicitly using carton.units_per_carton so
    we never accidentally compare cartons against pouches.
    """
    results = []

    for c_type, specs in CONTAINER_TYPES.items():
        container_dims = (specs["length_cm"], specs["width_cm"])
        pallet_footprint = (
            120 if pallet.pallet_type == "EURO" else 121.9,
            80 if pallet.pallet_type == "EURO" else 101.6,
        )

        pallets_fit = _pallets_per_container(container_dims, pallet_footprint)
        if pallets_fit == 0:
            continue  # pallet doesn't fit this container type at all

        weight_per_container_kg = pallets_fit * pallet.total_weight_kg
        if weight_per_container_kg > specs["max_weight_kg"]:
            # reduce pallets to respect container weight limit
            max_pallets_by_weight = int(specs["max_weight_kg"] // pallet.total_weight_kg)
            pallets_fit = max(max_pallets_by_weight, 0)
            if pallets_fit == 0:
                continue

        cartons_per_container = pallets_fit * pallet.cartons_per_pallet
        units_per_container = cartons_per_container * carton.units_per_carton

        containers_required = math.ceil(total_units / units_per_container) if units_per_container else 0
        total_units_shipped = containers_required * units_per_container

        container_volume = specs["length_cm"] * specs["width_cm"] * specs["height_cm"]
        pallet_volume = pallet_footprint[0] * pallet_footprint[1] * pallet.pallet_height_cm
        used_volume = pallets_fit * pallet_volume
        utilization = round(used_volume / container_volume, 3)

        freight_cost = containers_required * FREIGHT_COST_USD[c_type]

        results.append(ContainerResult(
            container_type=c_type,
            pallets_per_container=pallets_fit,
            containers_required=containers_required,
            total_units_shipped=total_units_shipped,
            container_utilization=utilization,
            empty_space_pct=round((1 - utilization) * 100, 1),
            freight_cost_usd=freight_cost,
        ))

    return results


def recommend_best_container(pallet: PalletResult, carton: CartonResult,
                              total_units: int) -> ContainerResult:
    """
    Picks the container type with the LOWEST total freight cost for this
    shipment. This directly implements the PDF's final AI Logic step:
    'Compare Multiple Scenarios -> Recommend Lowest Cost Solution'
    """
    all_results = evaluate_all_containers(pallet, carton, total_units)
    if not all_results:
        raise ValueError("No container type could fit this pallet configuration")

    return min(all_results, key=lambda r: r.freight_cost_usd)
