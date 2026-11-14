"""
Economics and Impact API Endpoints.
"""

from fastapi import APIRouter, Query
from backend.services.economics.service import EconomicsService
from backend.services.environmental.service import EnvironmentalService
from backend.schemas.economics import EconomicsCalculationResult, LogisticsSavingsResult
from backend.schemas.environmental import EnvironmentalImpactResult

router = APIRouter(prefix="/economics", tags=["Economics & Impact"])


@router.get("/calculate", response_model=EconomicsCalculationResult)
def calculate_economics(
    stubble_tons: float = Query(..., ge=0.0),
    transport_cost: float = Query(0.0, ge=0.0),
    scenario: str = Query("Base Case"),
):
    """Calculates unit economics, production yields, revenues, costs, margins, and breakeven."""
    return EconomicsService.calculate_unit_economics(
        stubble_tons=stubble_tons, transport_cost=transport_cost, scenario_name=scenario
    )


@router.get("/logistics-savings", response_model=LogisticsSavingsResult)
def calculate_logistics_savings(mobile_cost: float = Query(..., ge=0.0), stubble_tons: float = Query(..., ge=0.0)):
    """Calculates cost reduction of mobile refineries vs centralized processing."""
    return EconomicsService.calculate_logistics_savings(mobile_cost=mobile_cost, stubble_tons=stubble_tons)


@router.get("/environmental-impact", response_model=EnvironmentalImpactResult)
def calculate_environmental_impact(stubble_tons: float = Query(..., ge=0.0), scenario: str = Query("Base Case")):
    """Calculates avoided CO2 emissions, coal replacement, and social impact indicators."""
    return EnvironmentalService.calculate_environmental_impact(stubble_tons=stubble_tons, scenario_name=scenario)
