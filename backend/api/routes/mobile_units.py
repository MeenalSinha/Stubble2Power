"""
Mobile Bio-Refinery Fleet API Routes.
Manages trailer-mounted mobile densifier registrations, operational specifications, and fleet readiness.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.deployment.refinery_service import MobileRefineryService
from backend.schemas.deployment import MobileRefineryCreate, MobileRefineryResponse
from backend.core.exceptions.base import ValidationError, NotFoundError

router = APIRouter(prefix="/mobile-units", tags=["Phase 11: Mobile Bio-Refinery Fleet"])


@router.post("/", response_model=MobileRefineryResponse, status_code=201)
def register_mobile_unit(payload: MobileRefineryCreate, db: Session = Depends(get_db)):
    """Registers a trailer-mounted mobile densification or pyrolysis unit into the active fleet."""
    try:
        service = MobileRefineryService(db)
        return service.register_unit(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/", response_model=List[MobileRefineryResponse])
def list_mobile_units(status: Optional[str] = None, technology: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists registered mobile bio-refineries in the fleet."""
    service = MobileRefineryService(db)
    return service.list_units(status=status, technology=technology)


@router.get("/{unit_id}", response_model=MobileRefineryResponse)
def get_mobile_unit(unit_id: int, db: Session = Depends(get_db)):
    """Retrieves operational details for a specific mobile unit."""
    try:
        service = MobileRefineryService(db)
        return service.get_unit(unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/{unit_id}/status", response_model=MobileRefineryResponse)
def update_unit_status(
    unit_id: int,
    status: str = Body(..., embed=True, description="New operational status"),
    db: Session = Depends(get_db),
):
    """Updates unit operational status (e.g. AVAILABLE, DEPLOYED, MAINTENANCE)."""
    try:
        service = MobileRefineryService(db)
        return service.update_status(unit_id, status)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)
