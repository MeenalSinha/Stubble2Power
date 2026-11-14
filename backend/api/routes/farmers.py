"""
Farmer Management API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.services.farmers.service import FarmerService
from backend.schemas.farmer import FarmerCreate, FarmerResponse
from backend.core.exceptions.base import ValidationError

router = APIRouter(prefix="/farmers", tags=["Agricultural Management"])


@router.post("/", response_model=FarmerResponse, status_code=201)
def create_farmer(farmer_in: FarmerCreate, db: Session = Depends(get_db)):
    """Registers a new farmer with spatial coordinates and stubble availability."""
    try:
        service = FarmerService(db)
        return service.register_farmer(farmer_in)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/", response_model=List[FarmerResponse])
def list_farmers(
    district: Optional[str] = Query(None),
    village: Optional[str] = Query(None),
    min_stubble: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists enrolled farmers with dynamic filtering."""
    service = FarmerService(db)
    return service.list_farmers(district=district, village=village, min_stubble=min_stubble)


@router.get("/stats")
def get_farmer_statistics(db: Session = Depends(get_db)):
    """Retrieves aggregated farm and biomass statistics."""
    service = FarmerService(db)
    return service.get_summary_stats()


@router.post("/import-csv")
async def import_farmers_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads and ingests farmer records from a CSV file."""
    content = await file.read()
    try:
        service = FarmerService(db)
        return service.import_farmers_csv(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
