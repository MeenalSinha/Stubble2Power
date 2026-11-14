"""
Biomass Estimation & Inventory Tracking API Routes.
Provides endpoints for mathematical residue estimation, lifecycle tracking, and regional availability summaries.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.biomass.estimation_service import BiomassEstimationService
from backend.services.biomass.inventory_service import BiomassInventoryService
from backend.schemas.biomass import (
    BiomassEstimationRequest,
    BiomassEstimateResponse,
    BiomassInventoryTransactionCreate,
    BiomassInventoryTransactionResponse,
    BiomassAvailabilitySummary,
)
from backend.core.exceptions.base import ValidationError, NotFoundError

router = APIRouter(prefix="/biomass", tags=["Phase 10: Biomass Availability & Inventory"])


@router.post("/estimate", response_model=BiomassEstimateResponse, status_code=201)
def generate_biomass_estimate(payload: BiomassEstimationRequest, db: Session = Depends(get_db)):
    """Calculates collectable crop residue, accounting for soil retention, fodder demand, and moisture."""
    try:
        service = BiomassEstimationService(db)
        return service.estimate_crop_biomass(
            farm_crop_id=payload.farm_crop_id,
            actual_grain_yield_tons=payload.actual_grain_yield_tons,
            moisture_pct=payload.moisture_content_pct,
            retained_override=payload.retained_fraction_override,
            competing_override=payload.competing_demand_fraction_override,
        )
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/estimates/{estimate_id}", response_model=BiomassEstimateResponse)
def get_biomass_estimate(estimate_id: int, db: Session = Depends(get_db)):
    """Retrieves an existing biomass estimate by ID."""
    try:
        service = BiomassEstimationService(db)
        return service.get_estimate(estimate_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/estimates/crop/{crop_id}", response_model=List[BiomassEstimateResponse])
def list_estimates_for_crop(crop_id: int, db: Session = Depends(get_db)):
    """Lists biomass estimates generated for a specific crop cultivation."""
    service = BiomassEstimationService(db)
    return service.list_estimates_for_crop(crop_id)


@router.post("/inventory/transaction", response_model=BiomassInventoryTransactionResponse, status_code=201)
def record_inventory_transaction(payload: BiomassInventoryTransactionCreate, db: Session = Depends(get_db)):
    """Transitions biomass quantity through an audited lifecycle stage (COMMITTED, ALLOCATED, PROCESSED)."""
    try:
        service = BiomassInventoryService(db)
        return service.record_transaction(payload)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/inventory/farm/{farm_id}", response_model=List[BiomassInventoryTransactionResponse])
def list_transactions_for_farm(farm_id: int, db: Session = Depends(get_db)):
    """Lists all inventory transactions associated with a farm."""
    service = BiomassInventoryService(db)
    return service.list_transactions_by_farm(farm_id)


@router.get("/summary", response_model=BiomassAvailabilitySummary)
def get_biomass_summary(
    region: Optional[str] = Query(None, description="Filter summary by state or district"),
    db: Session = Depends(get_db),
):
    """Retrieves aggregate biomass availability, commitments, and allocations across farms."""
    service = BiomassInventoryService(db)
    return service.get_regional_availability_summary(region=region)
