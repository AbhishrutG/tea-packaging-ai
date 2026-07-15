"""
main.py

WHAT THIS FILE DOES (small why):
This is the actual FastAPI application -- the "waiter" from our restaurant
analogy. It defines every URL (endpoint) the frontend can call, and for each
one: validates the input (via schemas.py), calls the right optimization
function (from services/), saves to the database if needed (via models.py),
and returns a response.

WHY THIS MATTERS (big why):
This file is the seam between everything we've built. Nothing in
services/ or models.py knows anything about HTTP, URLs, or JSON -- they're
pure Python. This file's ONLY job is translation: HTTP request in, Python
function call, Python result out, HTTP response out. Keeping that separation
(services do the thinking, main.py just routes) is what "clean architecture"
means in practice, and it's directly why we can unit-test services/ without
ever starting a web server.

HOW TO RUN THIS (for your own reference):
    uvicorn app.main:app --reload
`uvicorn` is the actual web server program that runs FastAPI apps (FastAPI
itself is just the toolkit -- uvicorn is what listens for real HTTP
requests on a port and hands them to FastAPI). `--reload` means it restarts
automatically when you save code changes, useful during development.

Then open http://127.0.0.1:8000/docs in a browser -- FastAPI auto-generates
that whole interactive documentation page from the code below. That's the
Swagger UI bonus feature, for free.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db, engine
from app.models.models import Base, Simulation, Result
from app.schemas import (
    SimulationCreate, SimulationOut, PackageOptimizeRequest,
    PackageDimensionsOut, ComparisonOut,
)
from app.services.package_optimizer import generate_package_options
from app.services.carton_optimizer import optimize_carton
from app.services.pallet_optimizer import optimize_pallet
from app.services.container_optimizer import evaluate_all_containers, recommend_best_container
from app.services.cost_calculator import run_current_vs_ai
from dataclasses import asdict

# Sets up basic logging -- the PDF's Assessment Guidelines explicitly expect
# "logging" as a production-quality practice. This prints info to the
# console for every request so issues can be traced.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tea_packaging_api")

# Creates all database tables on startup if they don't already exist.
# (In a real production app you'd use Alembic migrations instead of this,
# but for a same-day assessment this is a reasonable documented shortcut.)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tea Packaging Optimization API",
    description="AI-assisted packaging, carton, pallet, and container optimization for tea exports.",
    version="1.0.0",
)

# CORS = Cross-Origin Resource Sharing. Browsers block a frontend running on
# one URL (e.g. localhost:3000) from calling an API on a different URL
# (e.g. localhost:8000) UNLESS the API explicitly allows it. This middleware
# says "allow requests from anywhere" -- fine for an assessment/demo, but in
# real production you'd restrict allow_origins to your actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STANDALONE OPTIMIZER ENDPOINTS
# (let the frontend call individual optimization steps directly,
#  as required by the PDF's minimum endpoint list)
# ============================================================

@app.post("/optimize/package", response_model=List[PackageDimensionsOut], tags=["Optimize"])
def optimize_package_endpoint(payload: PackageOptimizeRequest):
    """
    Runs Module 1 only. Returns the best package option plus alternatives.
    `payload: PackageOptimizeRequest` means FastAPI automatically reads the
    JSON body of the request, validates it against our schema, and gives us
    a clean Python object -- if validation fails, FastAPI returns a 422
    error automatically, before this function body even runs.
    """
    logger.info(f"Package optimization requested: density={payload.tea_density_g_cm3}, weight={payload.package_weight_g}")
    options = generate_package_options(payload.tea_density_g_cm3, payload.package_weight_g)
    return [asdict(dims) for _, dims in options]


@app.post("/optimize/carton", tags=["Optimize"])
def optimize_carton_endpoint(payload: PackageOptimizeRequest):
    """Runs Module 1 + Module 2: best package, then fits it into a carton."""
    options = generate_package_options(payload.tea_density_g_cm3, payload.package_weight_g)
    _, best_package = options[0]
    carton = optimize_carton(best_package, payload.package_weight_g)
    return asdict(carton)


@app.post("/optimize/pallet", tags=["Optimize"])
def optimize_pallet_endpoint(payload: PackageOptimizeRequest):
    """Runs Modules 1-3: package -> carton -> pallet."""
    options = generate_package_options(payload.tea_density_g_cm3, payload.package_weight_g)
    _, best_package = options[0]
    carton = optimize_carton(best_package, payload.package_weight_g)
    pallet = optimize_pallet(carton, pallet_type="EURO")
    return asdict(pallet)


@app.post("/optimize/container", tags=["Optimize"])
def optimize_container_endpoint(payload: SimulationCreate):
    """
    Runs the FULL cascade (Modules 1-4) and returns ALL container type
    comparisons (20GP/40GP/40HC), plus which one is recommended.
    Needs shipment_quantity too, so it uses SimulationCreate, not the
    smaller PackageOptimizeRequest.
    """
    options = generate_package_options(payload.tea_density_g_cm3, payload.package_weight_g)
    _, best_package = options[0]
    carton = optimize_carton(best_package, payload.package_weight_g)
    pallet = optimize_pallet(carton, pallet_type="EURO")

    all_options = evaluate_all_containers(pallet, carton, payload.shipment_quantity)
    best = recommend_best_container(pallet, carton, payload.shipment_quantity)

    return {
        "all_options": [asdict(r) for r in all_options],
        "recommended": asdict(best),
    }


# ============================================================
# SIMULATION ENDPOINTS
# (the "save a full run to the database" endpoints)
# ============================================================

@app.post("/simulation", response_model=SimulationOut, tags=["Simulation"])
def create_simulation(payload: SimulationCreate, db: Session = Depends(get_db)):
    """
    THE MAIN ENDPOINT. Runs the full current-vs-AI pipeline (Module 5),
    saves both the input (Simulation row) and output (Result row) to the
    database, and returns the saved simulation.

    `db: Session = Depends(get_db)` is the dependency injection mentioned in
    database.py -- FastAPI runs get_db() for us and hands us a ready-to-use
    database session as `db`.
    """
    logger.info(f"Creating simulation for {payload.shipment_quantity} units")

    # 1. Save the input
    simulation = Simulation(
        tea_density_g_cm3=payload.tea_density_g_cm3,
        package_weight_g=payload.package_weight_g,
        shipment_quantity=payload.shipment_quantity,
        shipment_type=payload.shipment_type,
        package_shape=payload.package_shape,
        packaging_material=payload.packaging_material,
        target_market=payload.target_market,
    )
    db.add(simulation)
    db.commit()
    db.refresh(simulation)  # pulls back the auto-generated id and created_at

    # 2. Run the full optimization + comparison pipeline
    try:
        comparison = run_current_vs_ai(
            tea_density_g_cm3=payload.tea_density_g_cm3,
            package_weight_g=payload.package_weight_g,
            total_units=payload.shipment_quantity,
            material=payload.packaging_material,
        )
    except ValueError as e:
        # if optimization fails (e.g. impossible input), don't leave an
        # orphaned simulation row with no result -- roll back and report clearly
        db.delete(simulation)
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Get the full container comparison too (Module 6)
    package_options = generate_package_options(payload.tea_density_g_cm3, payload.package_weight_g)
    _, best_package = package_options[0]
    carton = optimize_carton(best_package, payload.package_weight_g)
    pallet = optimize_pallet(carton, pallet_type="EURO")
    all_containers = evaluate_all_containers(pallet, carton, payload.shipment_quantity)

    # 4. Save the output
    result = Result(
        simulation_id=simulation.id,
        ai_package_json=comparison["ai"]["package"],
        ai_carton_json=comparison["ai"]["carton"],
        ai_pallet_json=comparison["ai"]["pallet"],
        ai_container_json=comparison["ai"]["container"],
        ai_packaging_cost_usd=comparison["ai"]["packaging_cost_usd"],
        ai_total_cost_usd=comparison["ai"]["total_cost_usd"],
        current_package_json=comparison["current"]["package"],
        current_carton_json=comparison["current"]["carton"],
        current_pallet_json=comparison["current"]["pallet"],
        current_container_json=comparison["current"]["container"],
        current_packaging_cost_usd=comparison["current"]["packaging_cost_usd"],
        current_total_cost_usd=comparison["current"]["total_cost_usd"],
        improvement_pct_json=comparison["improvement_pct"],
        all_container_options_json=[asdict(r) for r in all_containers],
    )
    db.add(result)
    db.commit()

    return simulation


@app.get("/simulation", response_model=List[SimulationOut], tags=["Simulation"])
def list_simulations(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Returns recent simulations (for the PDF's Dashboard 'Recent Simulations'
    and History page). `skip`/`limit` are query parameters (e.g.
    /simulation?skip=0&limit=20) -- FastAPI reads these from the URL
    automatically because they're plain function arguments, not in a
    request body.
    """
    return db.query(Simulation).order_by(Simulation.created_at.desc()).offset(skip).limit(limit).all()


@app.get("/simulation/{simulation_id}", tags=["Simulation"])
def get_simulation(simulation_id: int, db: Session = Depends(get_db)):
    """
    Fetches one simulation AND its full result together -- powers the
    PDF's Results page and Current vs AI Comparison page for a specific run.
    `{simulation_id}` in the URL is a "path parameter" -- FastAPI extracts
    it automatically and converts it to an int (or returns a clean error
    if someone passes something that isn't a number).
    """
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if simulation is None:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")

    result = db.query(Result).filter(Result.simulation_id == simulation_id).first()

    return {
        "simulation": SimulationOut.model_validate(simulation),
        "result": {
            "ai": {
                "package": result.ai_package_json,
                "carton": result.ai_carton_json,
                "pallet": result.ai_pallet_json,
                "container": result.ai_container_json,
                "packaging_cost_usd": result.ai_packaging_cost_usd,
                "total_cost_usd": result.ai_total_cost_usd,
            },
            "current": {
                "package": result.current_package_json,
                "carton": result.current_carton_json,
                "pallet": result.current_pallet_json,
                "container": result.current_container_json,
                "packaging_cost_usd": result.current_packaging_cost_usd,
                "total_cost_usd": result.current_total_cost_usd,
            },
            "improvement_pct": result.improvement_pct_json,
            "all_container_options": result.all_container_options_json,
        } if result else None,
    }


@app.post("/compare", response_model=ComparisonOut, tags=["Simulation"])
def compare_current_vs_ai(payload: SimulationCreate):
    """
    Runs the current-vs-AI comparison WITHOUT saving to the database --
    useful for a "preview" feature on the frontend before the user commits
    to saving a full simulation. Directly exposes Module 5's core logic.
    """
    return run_current_vs_ai(
        tea_density_g_cm3=payload.tea_density_g_cm3,
        package_weight_g=payload.package_weight_g,
        total_units=payload.shipment_quantity,
        material=payload.packaging_material,
    )


@app.get("/", tags=["Health"])
def root():
    """Simple health-check endpoint -- confirms the API is running."""
    return {"status": "ok", "message": "Tea Packaging Optimization API is running"}
