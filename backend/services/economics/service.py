"""
Unit Economics and Logistics Simulation Service.
Eliminates magic numbers and connects directly to configuration architecture.
"""

from typing import Dict, Optional
from backend.core.config.settings import config_manager
from backend.schemas.economics import (
    EconomicsCalculationResult,
    ProductionSummary,
    RevenueBreakdown,
    CostBreakdown,
    FinancialMetrics,
    LogisticsSavingsResult,
)


class EconomicsService:
    @staticmethod
    def calculate_unit_economics(
        stubble_tons: float,
        assumptions: Optional[Dict[str, float]] = None,
        transport_cost: float = 0.0,
        scenario_name: str = "Base Case",
    ) -> EconomicsCalculationResult:
        """
        Calculates complete unit economics for on-site biomass processing.
        Maintains division-by-zero protection.
        """
        if assumptions is None:
            assumptions = config_manager.get_scenario_assumptions(scenario_name)

        stubble_tons = max(0.0, float(stubble_tons))
        transport_cost = max(0.0, float(transport_cost))
        stubble_kg = stubble_tons * 1000.0

        briquette_yield = float(assumptions.get("briquette_yield", 0.70))
        biochar_yield = float(assumptions.get("biochar_yield", 0.20))
        briquette_price = float(assumptions.get("briquette_price", 6.0))
        biochar_price = float(assumptions.get("biochar_price", 15.0))
        carbon_credit_price = float(assumptions.get("carbon_credit_per_ton", 500.0))
        processing_cost_rate = float(assumptions.get("processing_cost_per_ton", 800.0))
        farmer_payment_rate = float(assumptions.get("farmer_payment_per_ton", 1500.0))

        # Production
        briquette_prod_kg = stubble_kg * briquette_yield
        biochar_prod_kg = stubble_kg * biochar_yield

        # Revenues
        briquette_rev = briquette_prod_kg * briquette_price
        biochar_rev = biochar_prod_kg * biochar_price
        carbon_rev = stubble_tons * carbon_credit_price
        total_revenue = briquette_rev + biochar_rev + carbon_rev

        # Costs
        processing_cost = stubble_tons * processing_cost_rate
        farmer_payment = stubble_tons * farmer_payment_rate
        total_cost = processing_cost + farmer_payment + transport_cost

        # Profit & Metrics
        profit = total_revenue - total_cost
        margin = (profit / total_revenue * 100.0) if total_revenue > 0 else 0.0
        cost_per_ton = (total_cost / stubble_tons) if stubble_tons > 0 else 0.0
        revenue_per_ton = (total_revenue / stubble_tons) if stubble_tons > 0 else 0.0
        breakeven_tons = (total_cost / revenue_per_ton) if revenue_per_ton > 0 else 0.0

        return EconomicsCalculationResult(
            stubble_tons=stubble_tons,
            scenario=scenario_name,
            production=ProductionSummary(briquette_kg=briquette_prod_kg, biochar_kg=biochar_prod_kg),
            revenue=RevenueBreakdown(
                briquette=briquette_rev, biochar=biochar_rev, carbon=carbon_rev, total=total_revenue
            ),
            cost=CostBreakdown(
                processing=processing_cost, farmer_payment=farmer_payment, transport=transport_cost, total=total_cost
            ),
            metrics=FinancialMetrics(
                profit=profit,
                margin=margin,
                cost_per_ton=cost_per_ton,
                revenue_per_ton=revenue_per_ton,
                breakeven_tons=breakeven_tons,
            ),
        )

    @staticmethod
    def calculate_logistics_savings(
        mobile_cost: float,
        stubble_tons: float,
        haulage_distance_km: Optional[float] = None,
        freight_rate_per_km: Optional[float] = None,
        payload_capacity_tons: Optional[float] = None,
    ) -> LogisticsSavingsResult:
        """
        Calculates savings of decentralized mobile units vs centralized plant logistics.
        Replaces legacy hardcoded `stubble_tons * 100 * 150 / 10` with documented parameters.
        """
        if haulage_distance_km is None:
            haulage_distance_km = float(config_manager.get("logistics.central_plant.haulage_distance_km"))
        if freight_rate_per_km is None:
            freight_rate_per_km = float(config_manager.get("logistics.central_plant.freight_rate_per_km"))
        if payload_capacity_tons is None:
            payload_capacity_tons = float(config_manager.get("logistics.central_plant.payload_capacity_tons"))

        stubble_tons = max(0.0, float(stubble_tons))
        mobile_cost = max(0.0, float(mobile_cost))

        # Centralized plant logistics: (total stubble / payload per truck) * distance * freight rate
        truck_trips = stubble_tons / payload_capacity_tons if payload_capacity_tons > 0 else 0.0
        central_cost = truck_trips * haulage_distance_km * freight_rate_per_km

        savings = central_cost - mobile_cost
        reduction_pct = (savings / central_cost * 100.0) if central_cost > 0 else 0.0

        return LogisticsSavingsResult(
            mobile_cost=mobile_cost, central_cost=central_cost, savings=savings, reduction_pct=reduction_pct
        )
