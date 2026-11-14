"""
End-to-End Pipeline Integration Test for Phases 10, 11 & 12.
Verifies the complete workflow:
Farmer -> Farm -> Cultivation -> Harvest -> Biomass Estimation ->
Mobile Bio-Refinery Fleet -> Route Planning -> Techno-Economics -> LCA Impact.
Directly tests API route handlers across all 6 new Phase 10-12 modules.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.entities import Base
from backend.schemas.farmer import FarmerCreate
from backend.schemas.farm import FarmCreate, FarmCropCreate, HarvestRecordCreate
from backend.schemas.biomass import BiomassEstimationRequest
from backend.schemas.deployment import MobileRefineryCreate, DeploymentPlanCreate
from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate
from backend.api.routes import farmers, farms, biomass, mobile_units, deployments, advanced_economics, environmental_lca


@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session for route testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_complete_phase10_11_12_integrated_pipeline(db_session):
    # ---------------------------------------------------------
    # STEP 1: Register Farmer and Farm Parcel (Phase 10)
    # ---------------------------------------------------------
    farmer = farmers.create_farmer(
        FarmerCreate(
            name="Harpreet Singh Dhillon",
            phone="9876501234",
            district="Ludhiana",
            village="Mullanpur",
            acres=40.0,
            stubble_tons=90.0,
            latitude=30.8650,
            longitude=75.7200,
            harvest_date=date(2024, 10, 25),
        ),
        db=db_session,
    )
    assert farmer.id is not None
    assert farmer.name == "Harpreet Singh Dhillon"

    farm = farms.create_farm(
        FarmCreate(
            farmer_id=farmer.id,
            farm_name="Dhillon Model Farm East",
            total_acres=40.0,
            village="Mullanpur",
            district="Ludhiana",
            state="Punjab",
            latitude=30.8650,
            longitude=75.7200,
            soil_type="Clay Loam",
        ),
        db=db_session,
    )
    assert farm.id is not None
    assert farm.farm_name == "Dhillon Model Farm East"

    # ---------------------------------------------------------
    # STEP 2: Record Crop Cultivation & Harvest Event (Phase 10)
    # ---------------------------------------------------------
    crop = farms.add_crop_cultivation(
        farm.id,
        FarmCropCreate(
            farm_id=farm.id,
            crop_type="PADDY",
            cultivated_acres=35.0,
            crop_season="Kharif",
            crop_year=2024,
            sowing_date=date(2024, 6, 20),
            expected_harvest_date=date(2024, 10, 28),
            expected_yield_tons_per_acre=2.80,
        ),
        db=db_session,
    )
    assert crop.id is not None
    assert crop.crop_type == "PADDY"

    harvest = farms.record_crop_harvest(
        crop.id,
        HarvestRecordCreate(
            farm_crop_id=crop.id,
            harvest_date=date(2024, 10, 28),
            actual_grain_yield_tons=98.0,
            grain_moisture_pct=14.2,
            harvest_method="COMBINE_HARVESTER_SUPER_SMS",
            is_measured=True,
        ),
        db=db_session,
    )
    assert harvest.id is not None
    assert harvest.actual_grain_yield_tons == 98.0

    # ---------------------------------------------------------
    # STEP 3: Biomass Mathematical Estimation (Phase 10)
    # ---------------------------------------------------------
    estimate = biomass.generate_biomass_estimate(
        BiomassEstimationRequest(farm_crop_id=crop.id, actual_grain_yield_tons=98.0), db=db_session
    )
    assert estimate.id is not None
    net_biomass = estimate.net_usable_biomass_tons
    assert net_biomass > 80.0

    summary = biomass.get_biomass_summary(region="Ludhiana", db=db_session)
    assert summary.total_net_usable_tons == pytest.approx(net_biomass, 0.2)

    # ---------------------------------------------------------
    # STEP 4: Register Mobile Bio-Refinery Unit (Phase 11)
    # ---------------------------------------------------------
    unit = mobile_units.register_mobile_unit(
        MobileRefineryCreate(
            unit_code="MBR-PB-INT-01",
            name="Ludhiana Mobile Densifier 01",
            technology="BRIQUETTING",
            hourly_capacity_tons=2.5,
            daily_operating_hours=10.0,
            fuel_consumption_liters_per_ton=4.5,
            home_depot_name="Ludhiana Ag Hub Depot",
            home_latitude=30.9010,
            home_longitude=75.8573,
            max_travel_radius_km=40.0,
        ),
        db=db_session,
    )
    assert unit.id is not None
    assert unit.unit_code == "MBR-PB-INT-01"

    # ---------------------------------------------------------
    # STEP 5: Plan Deployment and Vehicle Routing (Phase 11)
    # ---------------------------------------------------------
    plan = deployments.generate_deployment_plan(
        DeploymentPlanCreate(
            name="Mullanpur Integrated Cluster Campaign",
            region="Ludhiana",
            date_start=date(2024, 10, 28),
            date_end=date(2024, 11, 4),
            unit_ids=[unit.id],
        ),
        strategy="BALANCED",
        db=db_session,
    )

    assert plan.id is not None
    assert plan.status == "OPTIMIZED"
    assert plan.total_biomass_assigned_tons > 0.0
    assert plan.total_route_distance_km > 0.0
    assert len(plan.assignments) >= 1
    assert len(plan.routes) >= 1

    routes = deployments.get_deployment_routes(plan.id, db=db_session)
    assert len(routes) >= 1
    assert len(routes[0].stops) >= 3  # Depot -> Farm -> Depot

    # ---------------------------------------------------------
    # STEP 6: Techno-Economic Decision Modeling (Phase 12)
    # ---------------------------------------------------------
    econ = advanced_economics.evaluate_financial_scenario(
        FinancialScenarioCreate(
            deployment_plan_id=plan.id,
            scenario_name="Base Case",
            biomass_processed_tons=plan.total_biomass_assigned_tons,
            briquette_price_per_ton=6000.0,
            biochar_price_per_ton=15000.0,
            farmer_procurement_price_per_ton=1500.0,
            diesel_price_per_liter=89.50,
            processing_capex_per_unit=2500000.0,
            wacc_discount_rate_pct=10.5,
        ),
        db=db_session,
    )

    assert econ.id is not None
    assert econ.total_revenue_inr > 0.0
    assert econ.gross_profit_inr > 0.0
    assert econ.break_even_tons > 0.0

    sens_factors = advanced_economics.calculate_sensitivity_tornado(econ.id, db=db_session)
    assert len(sens_factors) >= 4

    # ---------------------------------------------------------
    # STEP 7: Life Cycle Assessment & Environmental Accounting (Phase 12)
    # ---------------------------------------------------------
    lca = environmental_lca.conduct_life_cycle_assessment(
        EnvironmentalAssessmentCreate(
            deployment_plan_id=plan.id, biomass_diverted_tons=plan.total_biomass_assigned_tons
        ),
        db=db_session,
    )

    assert lca.id is not None
    assert lca.baseline_total_co2e_tons > 0.0
    assert lca.coal_displaced_tons > 0.0
    assert lca.biochar_stable_carbon_stored_co2e_tons > 0.0
    assert lca.net_avoided_co2e_tons > lca.baseline_total_co2e_tons
    assert lca.net_benefit_ratio > 1.2
    assert lca.carbon_credit_eligible_tons > 0.0

    system_boundary = environmental_lca.get_lca_system_boundary()
    assert "Open-Field" in system_boundary.baseline_pathway
