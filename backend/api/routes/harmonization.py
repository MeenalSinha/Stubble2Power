"""
Scientific MODIS-VIIRS Harmonization API Endpoints.
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.services.harmonization.engine import HarmonizationEngine
from backend.repositories.harmonization_repository import HarmonizationRepository
from backend.schemas.harmonization import HarmonizationRunResponse

router = APIRouter(prefix="/harmonization", tags=["Scientific Harmonization"])


@router.post("/run", response_model=HarmonizationRunResponse)
def execute_harmonization_run(
    name: str = "Manual Harmonization Run",
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    grid_resolution_deg: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Executes the cross-sensor harmonization engine over stored satellite observations."""
    engine = HarmonizationEngine(db)
    result = engine.execute_harmonization(
        name=name,
        date_start=date_start,
        date_end=date_end,
        grid_resolution_deg=grid_resolution_deg
    )
    return result


@router.get("/latest")
def get_latest_harmonization_run(db: Session = Depends(get_db)):
    """Retrieves metadata of the most recent harmonization execution."""
    repo = HarmonizationRepository(db)
    latest = repo.get_latest_run()
    if not latest:
        return {"status": "NO_RUNS_RECORDED"}
    return HarmonizationRunResponse.model_validate(latest)
