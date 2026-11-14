"""
Pydantic schemas for Unit Economics and Scenario Modeling.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ProductionSummary(BaseModel):
    briquette_kg: float = Field(..., description="Quantity of briquettes produced in kg")
    biochar_kg: float = Field(..., description="Quantity of biochar produced in kg")


class RevenueBreakdown(BaseModel):
    briquette: float = Field(..., description="Revenue from briquette sales in INR")
    biochar: float = Field(..., description="Revenue from biochar sales in INR")
    carbon: float = Field(..., description="Revenue from carbon credits in INR")
    total: float = Field(..., description="Total gross revenue in INR")


class CostBreakdown(BaseModel):
    processing: float = Field(..., description="Operational processing cost in INR")
    farmer_payment: float = Field(..., description="Direct farmer payments in INR")
    transport: float = Field(..., description="Logistics and transport cost in INR")
    total: float = Field(..., description="Total operating cost in INR")


class FinancialMetrics(BaseModel):
    profit: float = Field(..., description="Net gross profit in INR")
    margin: float = Field(..., description="Operating margin percentage")
    cost_per_ton: float = Field(..., description="Cost per ton of stubble in INR/ton")
    revenue_per_ton: float = Field(..., description="Revenue per ton of stubble in INR/ton")
    breakeven_tons: float = Field(..., description="Minimum stubble tonnage required to break even")


class EconomicsCalculationResult(BaseModel):
    stubble_tons: float
    scenario: str
    production: ProductionSummary
    revenue: RevenueBreakdown
    cost: CostBreakdown
    metrics: FinancialMetrics


class LogisticsSavingsResult(BaseModel):
    mobile_cost: float
    central_cost: float
    savings: float
    reduction_pct: float
