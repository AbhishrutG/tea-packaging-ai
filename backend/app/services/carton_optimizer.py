"""
carton_optimizer.py

WHAT THIS FILE DOES (small why):
Takes the pouch dimensions from Module 1 and figures out how many pouches fit
into a carton box, in which orientation, so we waste the least space and don't
exceed a safe carton weight for handling.

WHY THIS MATTERS (big why):
This is step 2 of the cascade:
  Package -> Optimize Carton -> Optimize Pallet -> Optimize Container -> ...
A carton is just a bigger box. Fitting rectangular pouches into a bigger
rectangular box is a classic "3D bin packing" style problem. We don't need a
heavy optimization library for this specific case because pouches are boxes
and cartons are boxes -- axis-aligned grid packing (like stacking Lego bricks
in neat rows) gives the true optimum here, unlike the package-shape problem
which needed a continuous search.
"""

from dataclasses import dataclass
from itertools import permutations

from app.services.package_optimizer import PackageDimensions


# Standard board grades and their max safe carton weight (kg) - simplified assumption,
# documented in README. Real freight companies would have more precise tables.
BOARD_GRADES = [
    {"grade": "3-ply (light)", "max_weight_kg": 10},
    {"grade": "5-ply (standard)", "max_weight_kg": 20},
    {"grade": "7-ply (heavy duty)", "max_weight_kg": 30},
]

# Candidate carton envelope sizes to try (cm). Real systems might pull these
# from a catalog; we generate a few realistic standard sizes.
CANDIDATE_CARTON_SIZES_CM = [
    (30, 20, 20),
    (40, 30, 25),
    (50, 35, 30),
    (60, 40, 35),
]


@dataclass
class CartonResult:
    carton_length_cm: float
    carton_width_cm: float
    carton_height_cm: float
    units_per_carton: int
    fill_ratio: float          # how much of the carton's volume is actually used by pouches
    carton_weight_kg: float
    board_grade: str


def _units_that_fit(carton_dims: tuple[float, float, float],
                     package_dims: tuple[float, float, float]) -> int:
    """
    Tries every way the pouch can be rotated (6 orientations, since a box
    has 6 faces it could rest on) inside the carton, and for each orientation
    computes how many whole pouches fit along each axis using simple integer
    division -- like asking "how many 5cm blocks fit along a 27cm shelf?"
    (answer: 5, because we can't use partial blocks).

    Returns the BEST (maximum) units achievable across all orientations.
    """
    cl, cw, ch = carton_dims
    best_units = 0

    for orientation in set(permutations(package_dims)):
        pl, pw, ph = orientation
        if pl <= 0 or pw <= 0 or ph <= 0:
            continue
        n_l = int(cl // pl)
        n_w = int(cw // pw)
        n_h = int(ch // ph)
        units = n_l * n_w * n_h
        best_units = max(best_units, units)

    return best_units


def _pick_board_grade(carton_weight_kg: float) -> str:
    for board in BOARD_GRADES:
        if carton_weight_kg <= board["max_weight_kg"]:
            return board["grade"]
    return BOARD_GRADES[-1]["grade"]  # heaviest grade as fallback


def optimize_carton(package: PackageDimensions, package_weight_g: float) -> CartonResult:
    """
    Tries each candidate carton size, computes how many pouches fit, and picks
    the carton size that gives the BEST fill ratio (least wasted space) while
    keeping total carton weight within a safe handling limit.

    "Best" here = highest fill_ratio among cartons that don't exceed max board
    weight for their grade. This mirrors a real packer's decision: don't just
    cram in the most units, make sure a person can still safely lift the box.
    """
    package_dims = (package.length_cm, package.width_cm, package.height_cm)
    package_volume = package.volume_cm3

    best_result: CartonResult | None = None

    for carton_dims in CANDIDATE_CARTON_SIZES_CM:
        units = _units_that_fit(carton_dims, package_dims)
        if units == 0:
            continue  # pouch doesn't fit in this carton at all, skip

        carton_volume = carton_dims[0] * carton_dims[1] * carton_dims[2]
        used_volume = units * package_volume
        fill_ratio = round(used_volume / carton_volume, 3)

        carton_weight_kg = round((units * package_weight_g) / 1000, 2)
        board_grade = _pick_board_grade(carton_weight_kg)

        # skip cartons that would need a heavier grade than our heaviest option
        # (i.e. too heavy to be handled safely at all)
        if carton_weight_kg > BOARD_GRADES[-1]["max_weight_kg"]:
            continue

        candidate = CartonResult(
            carton_length_cm=carton_dims[0],
            carton_width_cm=carton_dims[1],
            carton_height_cm=carton_dims[2],
            units_per_carton=units,
            fill_ratio=fill_ratio,
            carton_weight_kg=carton_weight_kg,
            board_grade=board_grade,
        )

        if best_result is None or candidate.fill_ratio > best_result.fill_ratio:
            best_result = candidate

    if best_result is None:
        raise ValueError("No candidate carton size could fit this package safely")

    return best_result
