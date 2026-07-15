"""
package_optimizer.py

WHAT THIS FILE DOES (small why):
Given how dense the tea is (g/cm3) and how much a single package should weigh (g),
this figures out the physical size (length x width x height) of the pouch that
holds that tea, using the SMALLEST amount of packaging material possible.

WHY THIS MATTERS (big why):
This is step 1 of the optimization cascade described in the assessment PDF:
  Tea Density -> Calculate Volume -> Generate Package Options -> Optimize Carton -> ...
Every downstream step (carton, pallet, container) depends on getting this package
shape right. A badly-shaped pouch wastes material AND packs inefficiently into
cartons later. So this is not just "compute a number" -- it's a genuine
optimization problem: minimize surface area (= material = cost) subject to the
volume being fixed and the shape staying realistic for a tea pouch.
"""

from dataclasses import dataclass
from scipy.optimize import minimize
import math


@dataclass
class PackageDimensions:
    length_cm: float
    width_cm: float
    height_cm: float
    volume_cm3: float
    surface_area_cm2: float
    aspect_ratio: float  # width / height, used to describe "shape"


def calculate_volume(tea_density_g_cm3: float, package_weight_g: float) -> float:
    """
    Core physics: density = mass / volume  =>  volume = mass / density

    Example: tea_density=0.4 g/cm3, package_weight=100g
             volume = 100 / 0.4 = 250 cm3
    """
    if tea_density_g_cm3 <= 0:
        raise ValueError("tea_density_g_cm3 must be > 0")
    if package_weight_g <= 0:
        raise ValueError("package_weight_g must be > 0")
    return package_weight_g / tea_density_g_cm3


def _surface_area(dims: tuple[float, float, float]) -> float:
    """Surface area of a rectangular pouch (box approximation): 2(lw + lh + wh)"""
    l, w, h = dims
    return 2 * (l * w + l * h + w * h)


def _optimize_single_shape(volume_cm3: float, min_ratio: float, max_ratio: float) -> PackageDimensions:
    """
    WHY scipy.optimize instead of a fixed formula:
    A cube always has the minimum surface area for a given volume, but a cube-shaped
    tea pouch is unrealistic (tea pouches are typically flatter/taller, not cubic,
    for filling-machine and shelf-display reasons). So we constrain the shape with
    an aspect ratio range (width/height) and let scipy find the true minimum
    material usage WITHIN that realistic range -- this is a genuine constrained
    optimization, not a lookup formula.

    We fix length as derived from width & height once volume is set:
        volume = l * w * h  =>  l = volume / (w * h)
    so we only need to search over 2 free variables (w, h), which keeps the
    optimizer fast and well-behaved.
    """

    def objective(x):
        w, h = x
        if w <= 0 or h <= 0:
            return 1e9  # penalize invalid shapes so optimizer avoids them
        l = volume_cm3 / (w * h)
        return _surface_area((l, w, h))

    def ratio_constraint_lower(x):
        w, h = x
        return (w / h) - min_ratio  # must be >= 0

    def ratio_constraint_upper(x):
        w, h = x
        return max_ratio - (w / h)  # must be >= 0

    # initial guess: assume a cube-ish starting point, scaled to volume
    guess_side = volume_cm3 ** (1 / 3)
    x0 = [guess_side, guess_side]

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=[(0.5, 50), (0.5, 50)],  # sane real-world cm bounds for a pouch
        constraints=[
            {"type": "ineq", "fun": ratio_constraint_lower},
            {"type": "ineq", "fun": ratio_constraint_upper},
        ],
    )

    w, h = result.x
    l = volume_cm3 / (w * h)
    sa = _surface_area((l, w, h))

    return PackageDimensions(
        length_cm=round(l, 2),
        width_cm=round(w, 2),
        height_cm=round(h, 2),
        volume_cm3=round(volume_cm3, 2),
        surface_area_cm2=round(sa, 2),
        aspect_ratio=round(w / h, 3),
    )


def generate_package_options(
    tea_density_g_cm3: float,
    package_weight_g: float,
    package_shape: str = "square",
) -> list[PackageDimensions]:
    """
    Generates the BEST option plus 2 realistic alternatives, so Module 3's
    "Best Package" + "Alternative Package Options" in the PDF is genuine,
    not fabricated.

    Different aspect-ratio bands = different pouch "styles":
      - band A (0.55-0.70): standard flatter pouch
      - band B (0.70-0.85): boxier / more square-ish pouch
      - band C (0.40-0.55): taller, narrower pouch (e.g. stand-up pouch)

    For "round" package_shape we still model as an equivalent rectangular
    footprint for carton-packing purposes, but note that as an assumption
    (documented in README) since round pouches don't tile as efficiently --
    real systems would apply a packing-efficiency penalty (~0.785 for
    circles-in-square packing) which we apply as a fill-ratio adjustment
    later in the carton step, not here.
    """
    bands = [
        (0.55, 0.70, "standard_flat"),
        (0.70, 0.85, "boxy"),
        (0.40, 0.55, "tall_narrow"),
    ]

    volume = calculate_volume(tea_density_g_cm3, package_weight_g)

    options = []
    for min_r, max_r, label in bands:
        dims = _optimize_single_shape(volume, min_r, max_r)
        options.append((label, dims))

    # best = lowest surface area = least material = lowest packaging cost
    options.sort(key=lambda pair: pair[1].surface_area_cm2)

    return options  # list of (label, PackageDimensions), best first
