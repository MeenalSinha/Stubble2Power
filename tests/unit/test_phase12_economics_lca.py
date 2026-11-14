"""
Unit Tests for Phase 12: Advanced Techno-Economics & LCA Environmental Impact Intelligence.
Tests capital budgeting, break-even analysis, multi-year DCF (NPV/IRR), sensitivity tornado modeling,
IPCC AR6 cradle-to-grave LCA net emissions, and carbon-credit eligibility separation.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.entities import Base
from backend.services.economics.financial_engine import FinancialEngineService
from backend.services.environmental.lca_engine import LifeCycleAssessmentService
from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_techno_economic_evaluation_base_case(db_session):
    econ_svc = FinancialEngineService(db_session)
    payload = FinancialScenarioCreate(
        scenario_name="Base Case",
        biomass_processed_tons=500.0,
        briquette_price_per_ton=6000.0,
        biochar_price_per_ton=15000.0,
        farmer_procurement_price_per_ton=1500.0,
        diesel_price_per_liter=89.50,
        processing_capex_per_unit=2500000.0,
        wacc_discount_rate_pct=10.5,
    )
    result = econ_svc.evaluate_scenario(payload)

    assert result.id is not None
    assert result.total_biomass_processed_tons == 500.0
    # Physical revenues: 500 * 0.70 * 6000 = 2,100,000 + 500 * 0.20 * 15000 = 1,500,000 = 3,600,000
    assert result.total_revenue_inr == pytest.approx(3600000.0, 1000.0)
    # Total OPEX includes farmer payments (500 * 1500 = 750,000) + transport + processing
    assert result.total_farmer_payments_inr == pytest.approx(750000.0, 100.0)
    assert result.total_opex_inr > result.total_farmer_payments_inr
    assert result.gross_profit_inr > 0.0
    assert result.net_margin_pct > 20.0  # Profitable operations
    assert result.break_even_tons > 0.0
    assert result.cost_per_ton_processed_inr > 0.0
    assert result.payback_period_years > 0.0
    assert result.npv_inr is not None
    assert result.irr_pct > 0.0


def test_preset_scenario_comparison(db_session):
    econ_svc = FinancialEngineService(db_session)
    summary = econ_svc.compare_preset_scenarios(biomass_tons=1000.0)

    assert len(summary.scenarios) == 3
    names = [s.scenario_name for s in summary.scenarios]
    assert "Conservative" in names
    assert "Base Case" in names
    assert "Optimistic" in names

    # Revenue ordering: Optimistic > Base Case > Conservative
    sc_map = {s.scenario_name: s for s in summary.scenarios}
    assert sc_map["Optimistic"].total_revenue_inr > sc_map["Base Case"].total_revenue_inr
    assert sc_map["Base Case"].total_revenue_inr > sc_map["Conservative"].total_revenue_inr
    assert summary.most_profitable_scenario == "Optimistic"


def test_sensitivity_analysis_tornado(db_session):
    econ_svc = FinancialEngineService(db_session)
    base = econ_svc.evaluate_scenario(FinancialScenarioCreate(scenario_name="Base Case", biomass_processed_tons=500.0))

    tornado = econ_svc.calculate_sensitivity(base.id, variations=[-0.10, 0.10])
    assert len(tornado) == 8  # 4 parameters * 2 variations

    for factor in tornado:
        assert factor.parameter_name in [
            "Briquette Sale Price",
            "Biochar Sale Price",
            "Farmer Procurement Price",
            "Diesel Fuel Price",
        ]
        if "Price" in factor.parameter_name and "Sale" in factor.parameter_name:
            # Positive variation should increase profit
            if factor.variation_pct > 0:
                assert factor.resulting_profit_inr >= base.gross_profit_inr
        elif "Procurement" in factor.parameter_name or "Diesel" in factor.parameter_name:
            # Positive cost variation should decrease profit
            if factor.variation_pct > 0:
                assert factor.resulting_profit_inr <= base.gross_profit_inr


def test_lca_net_emissions_and_carbon_accounting(db_session):
    lca_svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=500.0,
        transport_fuel_liters=600.0,
        processing_fuel_liters=2250.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.15,
    )
    res = lca_svc.conduct_lca(payload)

    assert res.id is not None
    assert res.biomass_diverted_tons == 500.0

    # 1. Baseline Open Burning: 500t * 1.46t CO2 = 730t CO2
    assert res.baseline_burning_co2_tons == pytest.approx(730.0, 1.0)
    assert res.baseline_burning_ch4_tons > 1.0
    assert res.baseline_burning_n2o_tons > 0.01
    assert res.baseline_burning_pm25_tons > 4.0
    # Baseline CO2e uses IPCC AR6 (CH4=27.9, N2O=273)
    assert res.baseline_total_co2e_tons > res.baseline_burning_co2_tons

    # 2. Project Lifecycle Emissions (Diesel combustion)
    # Total diesel = 600 + 2250 = 2850 L * 2.68 kg CO2/L / 1000 = 7.64 tCO2
    assert res.project_total_emissions_co2e_tons == pytest.approx(7.64, 0.2)

    # 3. Coal Displacement & Biochar Carbon Permanence
    # Briquettes = 350t -> Coal displaced = 350 * 0.82 = 287t -> Avoided CO2 = 287 * 2.12 = 608.44 tCO2
    assert res.coal_displaced_tons == pytest.approx(287.0, 1.0)
    assert res.avoided_coal_co2e_tons > 500.0

    # Biochar = 75t -> C stored = 75 * 0.72 = 54t C -> CO2e stored = 54 * (44/12) = 198 tCO2e
    assert res.biochar_stable_carbon_stored_co2e_tons == pytest.approx(198.0, 2.0)

    # 4. Net Environmental Benefit
    assert res.net_avoided_co2e_tons > res.baseline_total_co2e_tons
    assert res.net_benefit_ratio > 1.5

    # 5. Carbon Credit Eligibility Separation
    # Excludes biogenic short-cycle CO2; verifies additionality
    assert res.carbon_credit_eligible_tons > 0.0
    assert res.carbon_credit_eligible_tons < res.net_avoided_co2e_tons
    assert "IPCC" in res.methodology_provenance


def test_lca_system_boundary_summary():
    boundary = LifeCycleAssessmentService.get_system_boundary()
    assert "Open-Field" in boundary.baseline_pathway
    assert any("Coal Displacement" in p for p in boundary.project_pathways)
    assert "AR6" in boundary.gwp_version
    assert "CEA" in boundary.grid_emission_factor_source


def test_custom_scenario_and_negative_contribution_margin(db_session):
    econ_svc = FinancialEngineService(db_session)
    # Extremely low product prices leading to negative contribution margin
    payload = FinancialScenarioCreate(
        scenario_name="Stress Test High Cost",
        biomass_processed_tons=100.0,
        briquette_price_per_ton=500.0,
        biochar_price_per_ton=500.0,
        farmer_procurement_price_per_ton=3000.0,
        diesel_price_per_liter=120.0,
    )
    result = econ_svc.evaluate_scenario(payload)
    assert result.scenario_name == "Stress Test High Cost"
    assert result.gross_profit_inr < 0.0
    # Negative contribution margin should result in None break even (unattainable)
    assert result.break_even_tons is None
    assert result.assumptions_json["break_even_status"] == "NOT_ACHIEVABLE"
    assert result.assumptions_json["break_even_note"] == "Not achievable under current assumptions"
    assert result.payback_period_years == 0.0
    assert result.roi_pct == 0.0


def test_lca_modeled_transport_fuel_annotation(db_session):
    lca_svc = LifeCycleAssessmentService(db_session)
    # When transport fuel is not provided, it is estimated and flagged in evidence
    payload = EnvironmentalAssessmentCreate(biomass_diverted_tons=200.0)
    result = lca_svc.conduct_lca(payload)
    assert result.evidence_json.get("is_transport_fuel_modeled_estimate") is True
    assert "carbon_credit_category" in result.evidence_json
