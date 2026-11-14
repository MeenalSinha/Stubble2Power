"""
Life Cycle Assessment (LCA) & Net Environmental Accounting API Routes.
Provides endpoints for calculating avoided open-field burning emissions, coal displacement,
biochar 100-year stable carbon storage, and carbon-credit eligibility.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.environmental.lca_engine import LifeCycleAssessmentService
from backend.schemas.environmental_lca import (
    EnvironmentalAssessmentCreate,
    EnvironmentalAssessmentResponse,
    SystemBoundarySummary
)
from backend.core.exceptions.base import ValidationError, NotFoundError

router = APIRouter(prefix="/environmental", tags=["Phase 12: LCA Environmental Impact"])


@router.post("/lca", response_model=EnvironmentalAssessmentResponse, status_code=201)
def conduct_life_cycle_assessment(payload: EnvironmentalAssessmentCreate, db: Session = Depends(get_db)):
    """Computes cradle-to-grave net GHG benefits relative to open-field stubble burning."""
    try:
        service = LifeCycleAssessmentService(db)
        return service.conduct_lca(payload)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/assessments", response_model=List[EnvironmentalAssessmentResponse])
def list_environmental_assessments(db: Session = Depends(get_db)):
    """Lists completed environmental life cycle assessments."""
    service = LifeCycleAssessmentService(db)
    return service.list_assessments()


@router.get("/assessments/{assessment_id}", response_model=EnvironmentalAssessmentResponse)
def get_environmental_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Retrieves an existing LCA assessment by ID."""
    try:
        service = LifeCycleAssessmentService(db)
        return service.get_assessment(assessment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/system-boundary", response_model=SystemBoundarySummary)
def get_lca_system_boundary():
    """Returns official LCA system boundaries, IPCC GWP version, and emissions provenance."""
    return LifeCycleAssessmentService.get_system_boundary()
