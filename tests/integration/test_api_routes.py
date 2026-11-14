"""
API Route Integration Tests for Stubble2Power.
Verifies route handlers directly across Health, Configuration, Farmers,
Clustering, Economics, NASA Status, Harmonization, and Activity Calendar.
Validates schemas, business rules, error guards, and end-to-end data flow.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.models.database import Base
from backend.schemas.farmer import FarmerCreate
from backend.api.routes import (
    health,
    config,
    farmers,
    clustering,
    economics,
    nasa,
    harmonization,
    calendar,
    seasonal,
    anomalies,
    agriculture,
    farms,
    biomass,
    mobile_units,
    deployments,
    advanced_economics,
    environmental_lca,
)
from backend.schemas.farm import FarmCreate, FarmCropCreate
from backend.schemas.biomass import BiomassEstimationRequest
from backend.schemas.deployment import MobileRefineryCreate
from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate


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


class TestAPIRouteHandlers:
    def test_health_route(self):
        result = health.get_health_status()
        assert result["status"] in ["healthy", "degraded"]
        assert result["api_version"] in ["2.0.0", "2.5.0"]
        assert "database_connected" in result
        assert "nasa_firms_configured" in result

    def test_config_registry_routes(self):
        # 1. List all configuration parameters
        all_configs = config.list_configuration()
        assert len(all_configs) >= 40
        assert "nasa.harmonization.grid_resolution_deg" in all_configs
        assert "nasa.harmonization.modis_detection_weight" in all_configs
        assert "scenario.base_case.briquette_price" in all_configs

        # 2. Get specific valid parameter
        param = config.get_configuration_parameter("nasa.harmonization.modis_detection_weight")
        assert param["name"] == "nasa.harmonization.modis_detection_weight"
        assert param["value"] == 2.5
        assert param["validation_min"] == 1.0

        # 3. Requesting an invalid parameter raises HTTPException 404
        with pytest.raises(HTTPException) as exc_info:
            config.get_configuration_parameter("non_existent_key")
        assert exc_info.value.status_code == 404

    def test_farmer_crud_routes(self, db_session):
        # 1. Register a new farmer
        new_farmer = FarmerCreate(
            name="Route Test Farmer",
            village="VillageRoute",
            district="Ludhiana",
            state="Punjab",
            country="IND",
            acres=15.0,
            stubble_tons=10.0,
            harvest_date=date(2025, 10, 25),
            latitude=30.9010,
            longitude=75.8573,
        )
        created = farmers.create_farmer(new_farmer, db_session)
        assert created.id > 0
        assert created.name == "Route Test Farmer"

        # 2. List farmers with village filter
        farmer_list = farmers.list_farmers(village="VillageRoute", db=db_session)
        assert len(farmer_list) == 1
        assert farmer_list[0].village == "VillageRoute"

        # 3. Summary stats route
        stats = farmers.get_farmer_statistics(db_session)
        assert stats["total_farmers"] == 1
        assert stats["total_stubble_tons"] == 10.0
        assert stats["total_acres"] == 15.0

    def test_clustering_route(self, db_session):
        # Seed 3 farmers
        for i in range(3):
            farmers.create_farmer(
                FarmerCreate(
                    name=f"Cluster Farmer {i}",
                    village=f"Village {i}",
                    district="Patiala",
                    state="Punjab",
                    country="IND",
                    acres=10.0,
                    stubble_tons=8.0,
                    harvest_date=date(2025, 10, 25),
                    latitude=30.33 + (i * 0.05),
                    longitude=76.38 + (i * 0.05),
                ),
                db_session,
            )

        # Execute clustering route
        res = clustering.run_clustering(n_clusters=2, scenario="Base Case", db=db_session)
        assert res.total_farmers == 3
        assert len(res.cluster_metrics) == 2
        assert res.total_mobile_transport_cost_inr >= 0.0

    def test_clustering_empty_data_raises_http_400(self, db_session):
        # Empty DB raises HTTPException 400
        with pytest.raises(HTTPException) as exc_info:
            clustering.run_clustering(n_clusters=2, scenario="Base Case", db=db_session)
        assert exc_info.value.status_code == 400

    def test_economics_routes(self):
        # 1. Unit economics calculation route
        econ_res = economics.calculate_economics(stubble_tons=100.0, transport_cost=500.0, scenario="Base Case")
        assert econ_res.stubble_tons == 100.0
        assert econ_res.production.briquette_kg == 70000.0
        assert econ_res.revenue.total > 0
        assert econ_res.metrics.profit > 0

        # 2. Logistics savings route
        log_res = economics.calculate_logistics_savings(mobile_cost=1500.0, stubble_tons=50.0)
        assert log_res.savings > 0
        assert log_res.reduction_pct > 0

        # 3. Environmental impact route
        env_res = economics.calculate_environmental_impact(stubble_tons=100.0, scenario="Base Case")
        assert env_res.co2_avoided == 150.0
        assert env_res.coal_replaced == 80.0
        assert env_res.trees_equivalent > 0

    def test_nasa_status_route(self, db_session):
        status = nasa.get_nasa_status(db_session)
        assert "supported_sources" in status
        assert "VIIRS_NOAA20_NRT" in status["supported_sources"]
        assert "stored_observations_summary" in status

    def test_harmonization_routes(self, db_session):
        # Run harmonization route on empty observations
        res = harmonization.execute_harmonization_run(name="Route Test Harmonization", db=db_session)
        assert res.status in ["COMPLETED", "COMPLETED_EMPTY"]
        assert "MODIS" in res.sensor_breakdown

        # Get latest run route
        latest = harmonization.get_latest_harmonization_run(db_session)
        assert latest is not None

    def test_calendar_routes(self, db_session):
        # 1. Daily calendar route
        daily = calendar.get_daily_calendar(date_start=date(2025, 10, 1), date_end=date(2025, 10, 5), db=db_session)
        assert len(daily) == 5
        assert all(d.coverage_status in ["NO_OVERPASS", "ZERO_BURNING", "COMPLETE"] for d in daily)

        # 2. Weekly calendar route
        weekly = calendar.get_weekly_calendar(year=2025, db=db_session)
        assert len(weekly) >= 50
        assert weekly[0].week_number == 1
        assert weekly[0].year == 2025

        # 3. Monthly calendar route
        monthly = calendar.get_monthly_calendar(year=2025, db=db_session)
        assert len(monthly) == 12
        assert monthly[0].month_name == "January"

        # 4. Annual summary route
        annual = calendar.get_annual_summary(year=2025, db=db_session)
        assert annual.year == 2025
        assert annual.burning_season_start == date(2025, 10, 1)

    def test_seasonal_routes(self, db_session):
        # 1. List seasonal profiles
        profiles = seasonal.get_seasonal_profiles(region_id="Punjab", db=db_session)
        assert isinstance(profiles, list)

        # 2. List baselines
        baselines = seasonal.get_historical_baselines(region_id="Punjab", db=db_session)
        assert isinstance(baselines, list)

    def test_anomalies_routes(self, db_session):
        # 1. List anomalies
        anom_list = anomalies.get_anomalies(region_id="Punjab", db=db_session)
        assert isinstance(anom_list, list)

    def test_agriculture_routes(self, db_session):
        # 1. List crop calendars
        calendars = agriculture.get_crop_calendars(state_name="Punjab", db=db_session)
        assert len(calendars) >= 4

        # 2. List assessments
        assessments = agriculture.get_assessments(db=db_session)
        assert isinstance(assessments, list)

        # 3. Get summary
        summary = agriculture.get_agricultural_summary(db=db_session)
        assert summary.total_assessed >= 0

    def test_farms_routes(self, db_session):
        farmer = farmers.create_farmer(
            FarmerCreate(
                name="Paramjit Singh",
                phone="9812345678",
                district="Sangrur",
                village="Sunam",
                acres=25.0,
                stubble_tons=50.0,
                latitude=30.1300,
                longitude=75.8000,
                harvest_date=date(2024, 10, 20),
            ),
            db=db_session,
        )

        farm = farms.create_farm(
            FarmCreate(
                farmer_id=farmer.id,
                farm_name="Sunam Parcel A",
                total_acres=25.0,
                village="Sunam",
                district="Sangrur",
                latitude=30.1300,
                longitude=75.8000,
            ),
            db=db_session,
        )
        assert farm.id is not None

        farm_list = farms.list_farms(district="Sangrur", db=db_session)
        assert len(farm_list) >= 1

        single_farm = farms.get_farm(farm.id, db=db_session)
        assert single_farm.farm_name == "Sunam Parcel A"

    def test_biomass_routes(self, db_session):
        farmer = farmers.create_farmer(
            FarmerCreate(
                name="Dalbir Singh",
                phone="9812345679",
                district="Patiala",
                village="Nabha",
                acres=20.0,
                stubble_tons=40.0,
                latitude=30.3700,
                longitude=76.1500,
                harvest_date=date(2024, 10, 22),
            ),
            db=db_session,
        )

        farm = farms.create_farm(
            FarmCreate(
                farmer_id=farmer.id,
                farm_name="Nabha Field 1",
                total_acres=20.0,
                village="Nabha",
                district="Patiala",
                latitude=30.3700,
                longitude=76.1500,
            ),
            db=db_session,
        )

        crop = farms.add_crop_cultivation(
            farm.id,
            FarmCropCreate(
                farm_id=farm.id, crop_type="PADDY", cultivated_acres=20.0, crop_season="Kharif", crop_year=2024
            ),
            db=db_session,
        )

        estimate = biomass.generate_biomass_estimate(
            BiomassEstimationRequest(farm_crop_id=crop.id, actual_grain_yield_tons=52.0), db=db_session
        )
        assert estimate.net_usable_biomass_tons > 0.0

        est_detail = biomass.get_biomass_estimate(estimate.id, db=db_session)
        assert est_detail.id == estimate.id

        est_crops = biomass.list_estimates_for_crop(crop.id, db=db_session)
        assert len(est_crops) >= 1

    def test_mobile_units_routes(self, db_session):
        unit = mobile_units.register_mobile_unit(
            MobileRefineryCreate(
                unit_code="MBR-RT-01",
                name="Route Test Unit",
                technology="BRIQUETTING",
                hourly_capacity_tons=2.5,
                daily_operating_hours=10.0,
                home_latitude=30.9000,
                home_longitude=75.8500,
            ),
            db=db_session,
        )
        assert unit.unit_code == "MBR-RT-01"

        unit_list = mobile_units.list_mobile_units(db=db_session)
        assert len(unit_list) >= 1

        retrieved = mobile_units.get_mobile_unit(unit.id, db=db_session)
        assert retrieved.name == "Route Test Unit"

    def test_deployments_routes(self, db_session):
        dep_list = deployments.list_deployments(db=db_session)
        assert isinstance(dep_list, list)

    def test_advanced_economics_routes(self, db_session):
        sc = advanced_economics.evaluate_financial_scenario(
            FinancialScenarioCreate(scenario_name="Base Case", biomass_processed_tons=300.0), db=db_session
        )
        assert sc.id is not None
        assert sc.total_revenue_inr > 0.0

        sc_list = advanced_economics.list_financial_scenarios(db=db_session)
        assert len(sc_list) >= 1

        sc_detail = advanced_economics.get_financial_scenario(sc.id, db=db_session)
        assert sc_detail.id == sc.id

    def test_environmental_lca_routes(self, db_session):
        lca = environmental_lca.conduct_life_cycle_assessment(
            EnvironmentalAssessmentCreate(biomass_diverted_tons=300.0), db=db_session
        )
        assert lca.id is not None
        assert lca.baseline_total_co2e_tons > 0.0

        lca_list = environmental_lca.list_environmental_assessments(db=db_session)
        assert len(lca_list) >= 1

        system_b = environmental_lca.get_lca_system_boundary()
        assert "Open-Field" in system_b.baseline_pathway
