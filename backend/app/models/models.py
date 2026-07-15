"""
models.py

WHAT THIS FILE DOES (small why):
Defines the database tables using SQLAlchemy ORM (Object-Relational Mapper --
lets us write Python classes that automatically become SQL tables, instead
of writing raw SQL by hand).

WHY THIS MATTERS (big why):
The PDF asks for tables covering: Users, Simulations, Tea Density,
Packaging Materials, Package Types, Cartons, Pallets, Containers, Results.

DESIGN DECISION (documented assumption for README):
We use a HYBRID approach, not full normalization:
  - Users, Simulations, PackagingMaterials get their own real tables
    (these have genuine independent identity and get queried directly,
    e.g. "show me all simulations for this user").
  - Package/Carton/Pallet/Container-per-simulation results are stored as
    JSON columns inside a single `Result` table linked to each Simulation,
    rather than 4 separate normalized tables with foreign keys.

WHY this hybrid choice instead of full normalization:
  A fully normalized schema (separate Package, Carton, Pallet, Container
  tables with foreign keys chaining together) would be "more correct" in a
  textbook sense, but in practice each simulation run produces ONE package
  config, ONE carton config, etc. -- they are never queried independently
  of their parent simulation, never shared between simulations, and never
  updated after creation. Normalizing data that's always read/written as a
  single unit adds JOIN complexity for zero real benefit. This is a common,
  defensible real-world trade-off (sometimes called "denormalization for
  read patterns") -- and it's exactly the kind of assumption the PDF asks
  us to document explicitly rather than hide.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, JSON, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """A registered user of the platform (basic auth - bonus feature)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    simulations = relationship("Simulation", back_populates="user")


class PackagingMaterial(Base):
    """
    Reference table: cost per cm2 for each material type (paper/plastic/metal).
    A real table (not JSON) because it's shared reference data queried by
    multiple simulations and might be edited by an admin over time.
    """
    __tablename__ = "packaging_materials"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)   # "paper", "plastic", "metal"
    cost_per_cm2_usd = Column(Float, nullable=False)


class Simulation(Base):
    """
    One "run" of the optimizer -- represents everything the PDF's Module 2
    (New Optimization) form collects as INPUT from the user.
    """
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable: allow anonymous/demo use

    tea_density_g_cm3 = Column(Float, nullable=False)
    package_weight_g = Column(Float, nullable=False)
    shipment_quantity = Column(Integer, nullable=False)
    shipment_type = Column(String, nullable=False)      # "total_weight" or "per_container"
    package_shape = Column(String, nullable=False)       # "square" or "round"
    packaging_material = Column(String, nullable=False)  # "paper" / "plastic" / "metal"
    target_market = Column(String, nullable=True)        # optional field per PDF

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="simulations")
    result = relationship("Result", back_populates="simulation", uselist=False)


class Result(Base):
    """
    The OUTPUT of running a simulation through the full optimization pipeline
    (Modules 3-7 of the PDF). One-to-one with a Simulation.

    Nested configs (package/carton/pallet/container, for both "current" and
    "ai") are stored as JSON here -- see the class docstring above for why.
    """
    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id"), unique=True, nullable=False)

    # AI (optimized) pipeline outputs
    ai_package_json = Column(JSON, nullable=False)
    ai_carton_json = Column(JSON, nullable=False)
    ai_pallet_json = Column(JSON, nullable=False)
    ai_container_json = Column(JSON, nullable=False)
    ai_packaging_cost_usd = Column(Float, nullable=False)
    ai_total_cost_usd = Column(Float, nullable=False)

    # Current (naive baseline) pipeline outputs -- for Module 7 comparison
    current_package_json = Column(JSON, nullable=False)
    current_carton_json = Column(JSON, nullable=False)
    current_pallet_json = Column(JSON, nullable=False)
    current_container_json = Column(JSON, nullable=False)
    current_packaging_cost_usd = Column(Float, nullable=False)
    current_total_cost_usd = Column(Float, nullable=False)

    # Pre-computed improvement percentages (Module 7 table)
    improvement_pct_json = Column(JSON, nullable=False)

    # All-container-types comparison (Module 6: 20GP vs 40GP vs 40HC)
    all_container_options_json = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    simulation = relationship("Simulation", back_populates="result")
