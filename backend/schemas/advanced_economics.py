"""
Pydantic Schemas for Advanced Techno-Economics and Financial Feasibility Modeling.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FinancialScenarioCreate(BaseModel):
    deployment_plan_id: Optional[int] = None
    scenario_name: str = "Base Case"  # Conservative, Base Case, Optimistic, Custom
    biomass_processed_tons: Optional[float] = None
    briquette_price_per_ton: Optional[float] = None
    biochar_price_per_ton: Optional[float] = None
    farmer_procurement_price_per_ton: Optional[float] = None
    diesel_price_per_liter: Optional[float] = None
    processing_capex_per_unit: Optional[float] = None
    wacc_discount_rate_pct: Optional[float] = None


class SensitivityFactor(BaseModel):
    parameter_name: str
    baseline_value: float
    variation_pct: float  # e.g. -20% or +20%
    resulting_profit_inr: float
    resulting_roi_pct: float
    profit_elasticity: float


class FinancialScenarioResponse(BaseModel):
    id: int
    deployment_plan_id: Optional[int] = None
    scenario_name: str
    briquette_price_per_ton: float
    biochar_price_per_ton: float
    farmer_procurement_price_per_ton: float
    diesel_price_per_liter: float
    processing_capex_per_unit: float
    wacc_discount_rate_pct: float
    total_biomass_processed_tons: float
    total_revenue_inr: float
    total_opex_inr: float
    total_farmer_payments_inr: float
    total_transport_costs_inr: float
    total_processing_costs_inr: float
    gross_profit_inr: float
    net_margin_pct: float
    cost_per_ton_processed_inr: float
    break_even_tons: float
    roi_pct: float
    payback_period_years: float
    npv_inr: float
    irr_pct: float
    assumptions_json: Dict[str, Any] = {}
    created_at: datetime


class FinancialComparisonSummary(BaseModel):
    scenarios: List[FinancialScenarioResponse]
    most_profitable_scenario: str
    highest_roi_scenario: str
