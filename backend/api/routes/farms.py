"""
Farm & Cultivation Intelligence API Routes.
Manages spatial farm boundaries, crop seasons, cultivation records, and harvest yield events.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.farms.farm_service import FarmService
from backend.schemas.farm import (
    FarmCreate,
    FarmResponse,
    FarmCropCreate,
    FarmCropResponse,
    HarvestRecordCreate,
    HarvestRecordResponse
)
from backend.core.exceptions.base import ValidationError, NotFoundError

router = APIRouter(prefix="/farms", tags=["Phase 10: Farm & Cultivation Intelligence"])


@router.post("/", response_model=FarmResponse, status_code=201)
def create_farm(payload: FarmCreate, db: Session = Depends(get_db)):
    """Registers a new farm polygon/centroid under an enrolled farmer."""
    try:
        service = FarmService(db)
        return service.create_farm(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/", response_model=List[FarmResponse])
def list_farms(
    farmer_id: Optional[int] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    soil_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists registered farm parcels with spatial attributes."""
    service = FarmService(db)
    return service.list_farms(farmer_id=farmer_id, district=district, state=state, soil_type=soil_type)


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    """Retrieves farm details by ID."""
    try:
        service = FarmService(db)
        return service.get_farm(farm_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/{farm_id}/crops", response_model=FarmCropResponse, status_code=201)
def add_crop_cultivation(farm_id: int, payload: FarmCropCreate, db: Session = Depends(get_db)):
    """Records a seasonal crop cultivation on a farm parcel."""
    try:
        service = FarmService(db)
        return service.add_crop_cultivation(farm_id, payload)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/{farm_id}/crops", response_model=List[FarmCropResponse])
def list_farm_crops(farm_id: int, db: Session = Depends(get_db)):
    """Lists crop cultivation cycles for a specific farm."""
    service = FarmService(db)
    return service.list_crops_by_farm(farm_id)


@router.post("/crops/{crop_id}/harvest", response_model=HarvestRecordResponse, status_code=201)
def record_crop_harvest(crop_id: int, payload: HarvestRecordCreate, db: Session = Depends(get_db)):
    """Logs an empirical harvest yield event and updates crop status."""
    try:
        service = FarmService(db)
        return service.record_harvest(crop_id, payload)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)
