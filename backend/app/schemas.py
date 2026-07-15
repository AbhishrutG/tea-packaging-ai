"""
schemas.py

WHAT THIS FILE DOES (small why):
Defines Pydantic models -- these are NOT database tables (that's models.py).
These are the "shape of data" for API requests and responses. FastAPI reads
these to automatically validate incoming data and generate documentation.

WHY THIS MATTERS (big why):
Without this file, if someone sent {"tea_density": "banana"} to our API, our
optimization code would crash with a confusing Python error deep inside
scipy. WITH Pydantic schemas, FastAPI catches the bad input immediately at
the "front door" and returns a clean error like:
  {"detail": [{"loc": ["tea_density_g_cm3"], "msg": "value is not a valid float"}]}
This is what "input validation" (mentioned as expected in the PDF's
Assessment Guidelines) actually looks like in FastAPI -- you get most of it
for free just by defining these classes correctly.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ---------- INPUT schemas (what the frontend SENDS to us) ----------

class SimulationCreate(BaseModel):
    """
    Matches the PDF's Module 2 'New Optimization' form exactly.
    Field(...) with gt=0 etc. adds validation rules -- FastAPI enforces
    these automatically, e.g. tea_density_g_cm3 must be greater than 0.
    """
    tea_density_g_cm3: float = Field(..., gt=0, description="Tea density in g/cm3")
    package_weight_g: float = Field(..., gt=0, description="Weight of a single package in grams")
    shipment_quantity: int = Field(..., gt=0, description="Total number of packages to ship")
    shipment_type: str = Field(default="total_weight", description="'total_weight' or 'per_container'")
    package_shape: str = Field(default="square", description="'square' or 'round'")
    packaging_material: str = Field(default="paper", description="'paper', 'plastic', or 'metal'")
    target_market: Optional[str] = Field(default=None, description="Optional target market name")


class PackageOptimizeRequest(BaseModel):
    """Input for the standalone POST /optimize/package endpoint."""
    tea_density_g_cm3: float = Field(..., gt=0)
    package_weight_g: float = Field(..., gt=0)


# ---------- OUTPUT schemas (what WE send back to the frontend) ----------

class PackageDimensionsOut(BaseModel):
    length_cm: float
    width_cm: float
    height_cm: float
    volume_cm3: float
    surface_area_cm2: float
    aspect_ratio: float


class SimulationOut(BaseModel):
    """
    What we send back after creating or fetching a simulation.
    `class Config: from_attributes = True` tells Pydantic it's allowed to
    read this data directly from a SQLAlchemy database object (not just
    from a plain dict) -- this is the bridge between models.py (database)
    and schemas.py (API).
    """
    id: int
    tea_density_g_cm3: float
    package_weight_g: float
    shipment_quantity: int
    shipment_type: str
    package_shape: str
    packaging_material: str
    target_market: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonOut(BaseModel):
    """Full current-vs-AI comparison result, matches PDF Module 7."""
    current: dict
    ai: dict
    improvement_pct: dict
