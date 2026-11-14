"""
NASA FIRMS Integration API Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.services.nasa.client import NASAClient
from backend.services.nasa.ingestion_service import IngestionService
from backend.repositories.satellite_repository import SatelliteRepository
from backend.schemas.satellite import IngestionJobResponse

router = APIRouter(prefix="/nasa", tags=["NASA Earth Observation"])


@router.get("/status")
def get_nasa_status(db: Session = Depends(get_db)):
    """Provides NASA FIRMS API connection status and stored observation metrics."""
    client = NASAClient()
    repo = SatelliteRepository(db)
    summary = repo.get_ingestion_summary()
    return {
        "is_configured": client.is_configured(),
        "base_url": client.base_url,
        "supported_sources": list(client.VALID_SOURCES.keys()),
        "stored_observations_summary": summary
    }


@router.post("/ingest/country", response_model=IngestionJobResponse)
def ingest_country_data(
    country_code: str = Query("IND"),
    source: str = Query("VIIRS_NOAA20_NRT"),
    day_range: int = Query(1, ge=1, le=10),
    date_str: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Triggers an ingestion job for a country from NASA FIRMS."""
    client = NASAClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="NASA FIRMS MAP_KEY is not configured in environment. Please set NASA_FIRMS_MAP_KEY."
        )

    svc = IngestionService(db, client)
    job = svc.run_country_ingestion(
        country_code=country_code,
        source=source,
        day_range=day_range,
        date_str=date_str
    )
    return job
