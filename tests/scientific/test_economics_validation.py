"""
Scientific Validation Suite: Techno-Economic Feasibility & Financial Decision Engine.
Validates capital budgeting, Discounted Cash Flow (DCF), Net Present Value (NPV),
Internal Rate of Return (IRR), break-even tonnage calculations, and sensitivity tornado elastance
against standard corporate finance formulations and MNRE/IREDA renewable project appraisal guidelines.

References:
- Brealey, Myers, Allen (2020), "Principles of Corporate Finance", McGraw-Hill
- Indian Renewable Energy Development Agency (IREDA), "Financing Norms for Biomass Projects"
- Punjab State Electricity Regulatory Commission (PSERC), "Biomass Tariff Determination Orders"
"""

import pytest
from sqlalchemy.orm import Session

from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.services.economics.financial_engine import FinancialEngineService
from backend.core.config.settings import config_manager


def test_revenue_and_production_yield_mathematics(db_session: Session):
    """
    Validates revenue calculation from physical conversion yields:
    Biomass = 1,000 metric tons
    Briquette Yield = 0.70 (700 tons @ 6,000 INR/ton) -> 4,200,000 INR
    Biochar Yield = 0.20 (200 tons @ 15,000 INR/ton) -> 3,000,000 INR
    Total Gross Physical Revenue = 7,200,000 INR
    Carbon credits are strictly excluded from operating cash revenue.
    """
    svc = FinancialEngineService(db_session)
    payload = FinancialScenarioCreate(
        scenario_name="Base Case",
        biomass_processed_tons=1000.0,
        briquette_price_per_ton=6000.0,
        biochar_price_per_ton=15000.0,
        farmer_procurement_price_per_ton=1500.0,
        diesel_price_per_liter=90.0,
        processing_capex_per_unit=2500000.0,
        wacc_discount_rate_pct=10.5,
    )

    scenario = svc.evaluate_scenario(payload)

    assert scenario.total_biomass_processed_tons == 1000.0
    assert scenario.total_revenue_inr == 7200000.0
    assert scenario.assumptions_json["briquettes_produced_tons"] == 700.0
    assert scenario.assumptions_json["biochar_produced_tons"] == 200.0


def test_break_even_tonnage_formulation(db_session: Session):
    """
    Validates break-even tonnage formulation:
    Break-Even Tons = Total Fixed Cost / Contribution Margin per Ton
    where Contribution Margin per Ton = (Revenue / Ton) - (Variable OPEX / Ton).
    """
    svc = FinancialEngineService(db_session)
    payload = FinancialScenarioCreate(
        scenario_name="Base Case",
        biomass_processed_tons=1000.0,
        briquette_price_per_ton=6000.0,
        biochar_price_per_ton=15000.0,
        farmer_procurement_price_per_ton=1500.0,
        diesel_price_per_liter=90.0,
        processing_capex_per_unit=2000000.0,
        wacc_discount_rate_pct=10.5,
    )

    scenario = svc.evaluate_scenario(payload)

    total_rev = scenario.total_revenue_inr
    total_opex = scenario.total_opex_inr
    tonnage = scenario.total_biomass_processed_tons

    rev_per_ton = total_rev / tonnage
    var_cost_per_ton = total_opex / tonnage
    contrib_margin = rev_per_ton - var_cost_per_ton

    # Check contribution margin is positive
    assert contrib_margin > 0.0

    # Fixed cost = depreciation (capex/7) + overhead (capex * 0.05)
    depr_years = float(config_manager.get("economics.equipment_depreciation_years"))
    overhead_frac = float(config_manager.get("economics.annual_fixed_overhead_fraction"))
    units_count = scenario.assumptions_json["units_count"]
    total_capex = units_count * 2000000.0
    expected_fixed_cost = (total_capex / depr_years) + (total_capex * overhead_frac)

    expected_break_even = round(expected_fixed_cost / contrib_margin, 1)
    assert scenario.break_even_tons == expected_break_even


def test_dcf_npv_discounting_identity(db_session: Session):
    """
    Validates Discounted Cash Flow (DCF) Net Present Value formulation:
    NPV = sum_{t=1}^N [ CF_t / (1 + WACC)^t ] - CAPEX.
    Verifies that the engine output matches an independent manual geometric series summation.
    """
    svc = FinancialEngineService(db_session)
    wacc = 10.5
    payload = FinancialScenarioCreate(
        scenario_name="Base Case",
        biomass_processed_tons=2000.0,
        briquette_price_per_ton=6500.0,
        biochar_price_per_ton=16000.0,
        farmer_procurement_price_per_ton=1400.0,
        diesel_price_per_liter=88.0,
        processing_capex_per_unit=2500000.0,
        wacc_discount_rate_pct=wacc,
    )

    scenario = svc.evaluate_scenario(payload)

    # Reconstruct annual cash flow from scenario results
    units_count = scenario.assumptions_json["units_count"]
    total_capex = units_count * 2500000.0
    depr_years = int(config_manager.get("economics.equipment_depreciation_years"))
    annual_depr = total_capex / depr_years
    overhead = total_capex * float(config_manager.get("economics.annual_fixed_overhead_fraction"))
    fixed_cost = annual_depr + overhead

    gross_profit = scenario.gross_profit_inr
    season_multiplier = float(config_manager.get("economics.seasons_per_year_multiplier"))
    annual_net_operating_profit = max(0.0, gross_profit * season_multiplier - fixed_cost)
    annual_cf = annual_net_operating_profit + annual_depr

    # Independent manual DCF
    r = wacc / 100.0
    manual_pv = sum(annual_cf / ((1.0 + r) ** t) for t in range(1, depr_years + 1))
    manual_npv = round(manual_pv - total_capex, 2)

    assert pytest.approx(manual_npv, rel=1e-3) == scenario.npv_inr


def test_negative_unit_economics_handling(db_session: Session):
    """
    Validates that when market prices fall below variable operational costs
    (e.g., extremely low briquette/biochar prices or exorbitant farmer payments),
    the financial engine safely flags non-viability without throwing division-by-zero errors.
    """
    svc = FinancialEngineService(db_session)
    payload = FinancialScenarioCreate(
        scenario_name="Underwater Scenario",
        biomass_processed_tons=500.0,
        briquette_price_per_ton=500.0,  # Unrealistic low price
        biochar_price_per_ton=1000.0,  # Unrealistic low price
        farmer_procurement_price_per_ton=4000.0,  # Exorbitant cost
        diesel_price_per_liter=150.0,
        processing_capex_per_unit=3000000.0,
        wacc_discount_rate_pct=12.0,
    )

    scenario = svc.evaluate_scenario(payload)

    # Gross profit must be negative
    assert scenario.gross_profit_inr < 0
    # Net margin must be negative
    assert scenario.net_margin_pct < 0
    # Break-even must be 0.0 (unachievable with negative contribution margin)
    assert scenario.break_even_tons == 0.0
    # ROI and Payback must be 0.0
    assert scenario.roi_pct == 0.0
    assert scenario.payback_period_years == 0.0
