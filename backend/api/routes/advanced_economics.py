"""
Advanced Techno-Economic Feasibility API Routes.
Provides endpoints for capital budgeting, break-even analysis, multi-year NPV/IRR, and sensitivity modeling.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.economics.financial_engine import FinancialEngineService
from backend.schemas.advanced_economics import (
    FinancialScenarioCreate,
    FinancialScenarioResponse,
    FinancialComparisonSummary,
    SensitivityFactor,
)
from backend.core.exceptions.base import ValidationError, NotFoundError

router = APIRouter(prefix="/economics", tags=["Phase 12: Techno-Economic Decision Support"])


@router.post("/scenario", response_model=FinancialScenarioResponse, status_code=201)
def evaluate_financial_scenario(payload: FinancialScenarioCreate, db: Session = Depends(get_db)):
    """Evaluates CAPEX/OPEX, break-even tonnage, margin, and investment returns for a biomass scenario."""
    try:
        service = FinancialEngineService(db)
        return service.evaluate_scenario(payload)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/scenarios", response_model=List[FinancialScenarioResponse])
def list_financial_scenarios(db: Session = Depends(get_db)):
    """Lists historically evaluated financial scenarios."""
    service = FinancialEngineService(db)
    return service.list_scenarios()


@router.get("/scenarios/{scenario_id}", response_model=FinancialScenarioResponse)
def get_financial_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Retrieves an evaluated financial scenario by ID."""
    try:
        service = FinancialEngineService(db)
        return service.get_scenario(scenario_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/compare", response_model=FinancialComparisonSummary)
def compare_scenarios(
    deployment_plan_id: Optional[int] = Query(None, description="Optional deployment plan to link"),
    biomass_tons: Optional[float] = Query(None, description="Biomass volume to model in tonnes"),
    db: Session = Depends(get_db),
):
    """Runs Conservative, Base Case, and Optimistic models side-by-side."""
    service = FinancialEngineService(db)
    return service.compare_preset_scenarios(deployment_plan_id=deployment_plan_id, biomass_tons=biomass_tons)


@router.get("/scenarios/{scenario_id}/sensitivity", response_model=List[SensitivityFactor])
def calculate_sensitivity_tornado(scenario_id: int, db: Session = Depends(get_db)):
    """Generates sensitivity tornado factors across key price, operational, and fuel parameters."""
    try:
        service = FinancialEngineService(db)
        return service.calculate_sensitivity(scenario_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
