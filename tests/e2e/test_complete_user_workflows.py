"""
End-to-End (E2E) Integration Workflow Test Suite.
Tests the complete multi-system platform pipelines connecting System A (NASA Earth Observation Intelligence)
and System B (Agricultural Waste Management & Clean Energy Production).

Workflows Covered:
1. NASA Fire Ingestion -> Normalization -> Harmonization -> Anomaly Detection
2. Agricultural Land-Use Context -> Cropland Masking -> Harvest Calendar Association
3. Farmer Registration -> Farm Parcels -> Harvest Yield Logging -> Automated Biomass Estimation
4. Biomass Inventory -> Fleet Selection -> 2-Opt Route Dispatch -> Collection Lifecycle
5. Deployment Plan -> Financial DCF Analysis -> Life Cycle Assessment (LCA)
6. Tenant Organization Creation -> User Registration -> JWT Authentication -> RBAC Enforcement
7. DPDP Consent Grant -> Dispatch Planning -> Consent Withdrawal -> Exclusion from Dispatch -> DSR Request
"""

from datetime import date, datetime
import pytest
from sqlalchemy.orm import Session

from backend.models.entities import (
    Farmer,
    Farm,
    FarmCrop,
    HarvestRecord,
    Organization,
    NormalizedSatelliteObservation,
    IngestionJob,
)
from backend.services.harmonization.engine import HarmonizationEngine
from backend.services.anomaly.detector import StatisticalAnomalyDetector
from backend.services.agriculture.classification_service import AgriculturalClassificationService
from backend.services.biomass.estimation_service import BiomassEstimationService
from backend.services.deployment.refinery_service import MobileRefineryService
from backend.services.deployment.planner_service import DeploymentPlannerService
from backend.services.economics.financial_engine import FinancialEngineService
from backend.services.environmental.lca_engine import LifeCycleAssessmentService
from backend.services.privacy.privacy_service import PrivacyService
from backend.services.auth.auth_service import AuthService
from backend.schemas.deployment import DeploymentPlanCreate, MobileRefineryCreate
from backend.schemas.auth import UserRegisterRequest, UserLoginRequest
from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate
from backend.core.security.auth import decode_token
from backend.core.security.rbac import has_permission, assert_permission
from backend.core.exceptions.base import AuthorizationError


def test_workflow_1_nasa_fire_harmonization_to_anomaly_detection(db_session: Session):
    """
    Workflow 1:
    Simulates NASA MODIS and VIIRS satellite observations -> Executes scientific harmonization ->
    Computes NBAI & consensus -> Feeds into Seasonal & Anomaly Detection engine.
    """
    # 1. Seed simulated normalized observations for Ludhiana grid
    obs_date = date(2025, 10, 28)
    job = IngestionJob(
        job_uuid="e2e-job-01",
        satellite="Terra",
        instrument="MODIS",
        source_endpoint="FIRMS_API",
        date_start=obs_date,
        date_end=obs_date,
        status="COMPLETED",
    )
    db_session.add(job)
    db_session.commit()

    modis_obs = NormalizedSatelliteObservation(
        source_record_hash="hash_modis_01",
        ingestion_job_id=job.id,
        instrument="MODIS",
        satellite="Terra",
        product_version="6.1NRT",
        latitude=30.850,
        longitude=75.850,
        acquisition_date=obs_date,
        acquisition_time_utc="0730",
        timestamp_utc=datetime(2025, 10, 28, 7, 30),
        confidence_raw="80",
        confidence_normalized=80.0,
        daynight="D",
        frp=45.0,
        spatial_grid_id="GRID_30.85_75.85",
        is_valid=True,
    )
    viirs_obs = NormalizedSatelliteObservation(
        source_record_hash="hash_viirs_01",
        ingestion_job_id=job.id,
        instrument="VIIRS",
        satellite="NOAA-20",
        product_version="2.0NRT",
        latitude=30.852,
        longitude=75.851,
        acquisition_date=obs_date,
        acquisition_time_utc="0815",
        timestamp_utc=datetime(2025, 10, 28, 8, 15),
        confidence_raw="high",
        confidence_normalized=90.0,
        daynight="D",
        frp=32.0,
        spatial_grid_id="GRID_30.85_75.85",
        is_valid=True,
    )
    db_session.add_all([modis_obs, viirs_obs])
    db_session.commit()

    # 2. Run Harmonization Engine
    harm_engine = HarmonizationEngine(db_session)
    run_resp = harm_engine.execute_harmonization(name="E2E Fire Harmonization", date_start=obs_date, date_end=obs_date)

    assert run_resp.status == "COMPLETED"
    assert run_resp.total_input_observations >= 2
    assert run_resp.harmonized_cells_count >= 1

    # 3. Feed to Statistical Anomaly Detector
    anomaly_detector = StatisticalAnomalyDetector(db_session)
    anomalies = anomaly_detector.detect_anomalies(
        date_start=obs_date, date_end=obs_date, region_id="Punjab", zscore_threshold=1.5
    )
    assert isinstance(anomalies, list)


def test_workflow_2_agricultural_context_and_harvest_association(db_session: Session):
    """
    Workflow 2:
    Validates agricultural land-use context classification, LULC cropland masking,
    and harvest calendar window correlation.
    """
    agri_svc = AgriculturalClassificationService(db_session)
    assessment = agri_svc.assess_observation(
        observation_date=date(2025, 10, 25),
        latitude=30.720,
        longitude=76.220,
        grid_id="GRID_30.72_76.22",
        frp_mw=35.0,
        state_name="Punjab",
    )

    assert assessment is not None
    assert assessment.land_use_class is not None
    assert assessment.context_classification is not None


def test_workflow_3_farmer_parcels_harvest_to_biomass_estimation(db_session: Session):
    """
    Workflow 3:
    Registers a farmer -> Adds farm parcel and crop record -> Logs measured grain harvest ->
    Executes automated biomass generation and verification.
    """
    # 1. Farmer Registration
    farmer = Farmer(
        name="Jaswant Singh",
        village="Jagraon",
        district="Ludhiana",
        state="Punjab",
        acres=30.0,
        stubble_tons=100.0,
        harvest_date=date(2025, 10, 22),
        latitude=30.780,
        longitude=75.480,
        consent_given=True,
    )
    db_session.add(farmer)
    db_session.commit()
    db_session.refresh(farmer)

    # 2. Farm Parcel & Crop Registration
    farm = Farm(
        farmer_id=farmer.id,
        farm_name="Jagraon Main Parcel",
        latitude=30.780,
        longitude=75.480,
        total_acres=30.0,
        village="Jagraon",
        district="Ludhiana",
        state="Punjab",
        ownership_status="OWNED",
        soil_type="ALLUVIAL",
        verification_status="VERIFIED",
    )
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)

    crop = FarmCrop(
        farm_id=farm.id,
        crop_type="PADDY_RICE",
        cultivated_acres=30.0,
        crop_season="KHARIF",
        crop_year=2025,
        expected_yield_tons_per_acre=2.5,
        sowing_date=date(2025, 6, 20),
        expected_harvest_date=date(2025, 10, 22),
        cultivation_status="ACTIVE",
    )
    db_session.add(crop)
    db_session.commit()
    db_session.refresh(crop)

    # 3. Log Measured Grain Harvest
    harvest = HarvestRecord(
        farm_crop_id=crop.id,
        harvest_date=date(2025, 10, 22),
        actual_grain_yield_tons=75.0,
        grain_moisture_pct=13.5,
        is_measured=True,
    )
    db_session.add(harvest)
    db_session.commit()

    # 4. Automated Biomass Estimation
    bio_svc = BiomassEstimationService(db_session)
    estimate = bio_svc.estimate_crop_biomass(farm_crop_id=crop.id, persist=True)

    # Gross: 75.0 * 1.50 = 112.5 tons
    assert estimate.gross_residue_tons == 112.50
    assert estimate.net_usable_biomass_tons > 0.0
    assert estimate.dry_matter_tons > 0.0
    assert estimate.confidence_score >= 0.95


def test_workflow_4_biomass_inventory_fleet_selection_to_route_dispatch(db_session: Session):
    """
    Workflow 4:
    Prepares candidate biomass inventory -> Deploys a Mobile Bio-Refinery unit ->
    Generates capacity-constrained 2-Opt collection route -> Transitions assignment status.
    """
    # 1. Register Mobile Bio-Refinery
    refinery_svc = MobileRefineryService(db_session)
    unit_create = MobileRefineryCreate(
        unit_code="E2E-REFINERY-01",
        name="AgriPower Mobile Densifier V3",
        hourly_capacity_tons=3.0,
        daily_operating_hours=10.0,
        fuel_consumption_liters_per_ton=3.5,
        operating_cost_per_hour_inr=850.0,
        home_depot_name="Ludhiana Central Depot",
        home_latitude=30.700,
        home_longitude=75.500,
        max_travel_radius_km=100.0,
    )
    unit = refinery_svc.register_unit(unit_create)
    assert unit.id is not None

    # 2. Register candidate farmer with harvest
    farmer = Farmer(
        name="Baldev Singh",
        village="Mullanpur",
        district="Ludhiana",
        state="Punjab",
        acres=15.0,
        stubble_tons=50.0,
        harvest_date=date(2025, 10, 25),
        latitude=30.820,
        longitude=75.650,
        consent_given=True,
    )
    db_session.add(farmer)
    db_session.commit()

    farm = Farm(
        farmer_id=farmer.id,
        farm_name="Mullanpur East",
        latitude=30.820,
        longitude=75.650,
        total_acres=15.0,
        village="Mullanpur",
        district="Ludhiana",
        state="Punjab",
        ownership_status="OWNED",
        soil_type="ALLUVIAL",
        verification_status="VERIFIED",
    )
    db_session.add(farm)
    db_session.commit()

    crop = FarmCrop(
        farm_id=farm.id,
        crop_type="PADDY_RICE",
        cultivated_acres=15.0,
        crop_season="KHARIF",
        crop_year=2025,
        expected_yield_tons_per_acre=2.5,
        expected_harvest_date=date(2025, 10, 25),
        cultivation_status="HARVESTED",
    )
    db_session.add(crop)
    db_session.commit()

    bio_svc = BiomassEstimationService(db_session)
    bio_svc.estimate_crop_biomass(farm_crop_id=crop.id, actual_grain_yield_tons=40.0, persist=True)

    # 3. Generate Deployment & Route Plan
    planner_svc = DeploymentPlannerService(db_session)
    plan_create = DeploymentPlanCreate(
        name="E2E Autumn Collection Schedule",
        date_start=date(2025, 10, 20),
        date_end=date(2025, 11, 15),
        region="Ludhiana",
    )
    plan = planner_svc.generate_deployment_plan(plan_create)

    assert plan.id is not None
    assert plan.total_biomass_assigned_tons > 0.0
    assert len(plan.assignments) >= 1
    assert len(plan.routes) >= 1

    # Verify 2-Opt road distance and fuel calculation
    route = plan.routes[0]
    assert route.total_distance_km > 0.0
    assert route.fuel_consumed_liters > 0.0


def test_workflow_5_deployment_to_financial_dcf_and_lca(db_session: Session):
    """
    Workflow 5:
    Takes an executed deployment plan -> Performs capital budgeting & DCF financial evaluation ->
    Conducts Life Cycle Assessment (LCA) environmental accounting.
    """
    # 1. Financial Evaluation
    fin_svc = FinancialEngineService(db_session)
    scenario_create = FinancialScenarioCreate(
        scenario_name="Base Case",
        biomass_processed_tons=1500.0,
        briquette_price_per_ton=6200.0,
        biochar_price_per_ton=15500.0,
        farmer_procurement_price_per_ton=1450.0,
        wacc_discount_rate_pct=10.5,
    )
    fin_scenario = fin_svc.evaluate_scenario(scenario_create)

    assert fin_scenario.total_revenue_inr > 0.0
    assert fin_scenario.gross_profit_inr > 0.0
    assert fin_scenario.break_even_tons > 0.0
    assert fin_scenario.npv_inr is not None
    assert fin_scenario.irr_pct >= 0.0

    # 2. Environmental Life Cycle Assessment (LCA)
    lca_svc = LifeCycleAssessmentService(db_session)
    lca_create = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1500.0,
        transport_fuel_liters=3500.0,
        processing_fuel_liters=5200.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20,
    )
    lca_assessment = lca_svc.conduct_lca(lca_create)

    assert lca_assessment.baseline_total_co2e_tons > 0.0
    assert lca_assessment.avoided_coal_co2e_tons > 0.0
    assert lca_assessment.biochar_stable_carbon_stored_co2e_tons > 0.0
    assert lca_assessment.net_avoided_co2e_tons > 0.0
    assert lca_assessment.carbon_credit_eligible_tons > 0.0


def test_workflow_6_multi_user_tenant_jwt_and_rbac(db_session: Session):
    """
    Workflow 6:
    Creates a tenant organization -> Registers users with distinct roles ->
    Issues cryptographically signed JWT tokens -> Verifies RBAC permission enforcement.
    """
    auth_svc = AuthService(db_session)

    # 1. Tenant Organization
    org = Organization(
        name="Daba Agro Cooperative",
        code="DABA-COOP-01",
        org_type="AGRICULTURAL_COOP",
        country="IND",
        domain="dabacoop.org",
        contact_email="admin@dabacoop.org",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # 2. Register Users
    user_farmer = auth_svc.register_user(
        UserRegisterRequest(
            username="farmer_kuldip",
            email="kuldip@dabacoop.org",
            password="SecurePassword@123",
            full_name="Kuldip Singh",
            role_name="FARMER",
            organization_id=org.id,
        )
    )

    user_operator = auth_svc.register_user(
        UserRegisterRequest(
            username="operator_surjit",
            email="surjit@dabacoop.org",
            password="SecurePassword@123",
            full_name="Surjit Kumar",
            role_name="FIELD_OPERATOR",
            organization_id=org.id,
        )
    )

    assert user_farmer.id is not None
    assert user_operator.id is not None

    # 3. Authenticate and verify JWT tokens
    login_resp = auth_svc.authenticate_user(UserLoginRequest(username="farmer_kuldip", password="SecurePassword@123"))
    assert login_resp.access_token is not None

    payload = decode_token(login_resp.access_token)
    assert payload["sub"] == "farmer_kuldip"
    assert payload["role"] == "FARMER"
    assert payload["organization_id"] == org.id

    # 4. RBAC Permission Checks
    # Farmer can edit own farm, but cannot manage organization members or allocate org biomass
    assert has_permission("FARMER", "farm:edit_own") is True
    assert has_permission("FARMER", "biomass:allocate_org") is False
    assert has_permission("FIELD_OPERATOR", "collection:update") is True
    assert has_permission("SYSTEM_ADMINISTRATOR", "system:admin") is True

    # Assert raises AuthorizationError on unauthorized action
    with pytest.raises(AuthorizationError):
        assert_permission("FARMER", "biomass:allocate_org")


def test_workflow_7_dpdp_consent_withdrawal_and_dispatch_exclusion(db_session: Session):
    """
    Workflow 7:
    Landholder registers with consent -> Harvests biomass -> Withdraws LOGISTICS_DISPATCH consent ->
    Deployment planner runs -> Verifies that the parcel is excluded from vehicle collection dispatch ->
    Landholder files a Data Subject Request (DSR).
    """
    priv_svc = PrivacyService(db_session)
    planner_svc = DeploymentPlannerService(db_session)

    # 1. Register Farmer
    farmer = Farmer(
        name="Harjit Kaur",
        village="Baddowal",
        district="Ludhiana",
        state="Punjab",
        acres=20.0,
        stubble_tons=60.0,
        harvest_date=date(2025, 10, 26),
        latitude=30.860,
        longitude=75.750,
        consent_given=True,
    )
    db_session.add(farmer)
    db_session.commit()
    db_session.refresh(farmer)

    farm = Farm(
        farmer_id=farmer.id,
        farm_name="Baddowal South Parcel",
        latitude=30.860,
        longitude=75.750,
        total_acres=20.0,
        village="Baddowal",
        district="Ludhiana",
        state="Punjab",
        ownership_status="OWNED",
        soil_type="ALLUVIAL",
        verification_status="VERIFIED",
    )
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)

    crop = FarmCrop(
        farm_id=farm.id,
        crop_type="PADDY_RICE",
        cultivated_acres=20.0,
        crop_season="KHARIF",
        crop_year=2025,
        expected_yield_tons_per_acre=2.5,
        expected_harvest_date=date(2025, 10, 26),
        cultivation_status="HARVESTED",
    )
    db_session.add(crop)
    db_session.commit()
    db_session.refresh(crop)

    bio_svc = BiomassEstimationService(db_session)
    bio_svc.estimate_crop_biomass(farm_crop_id=crop.id, actual_grain_yield_tons=50.0, persist=True)

    # 2. Record initial consent and register mobile refinery unit
    refinery_svc = MobileRefineryService(db_session)
    refinery_svc.register_unit(
        MobileRefineryCreate(
            unit_code="E2E-REFINERY-PRIVACY",
            name="AgriPower Mobile Densifier V3",
            hourly_capacity_tons=3.0,
            daily_operating_hours=10.0,
            fuel_consumption_liters_per_ton=3.5,
            operating_cost_per_hour_inr=850.0,
            home_depot_name="Ludhiana Central Depot",
            home_latitude=30.700,
            home_longitude=75.500,
            max_travel_radius_km=100.0,
        )
    )

    consent = priv_svc.record_consent(
        farmer_id=farmer.id,
        consent_purpose="LOGISTICS_DISPATCH",
        notes="Authorized for seasonal bio-refinery collection",
    )
    assert consent.is_granted is True

    # 3. Landholder exercises DPDP Section 6 right: WITHDRAW CONSENT
    withdrawn_consent = priv_svc.withdraw_consent(consent.id)
    assert withdrawn_consent.is_granted is False
    assert withdrawn_consent.withdrawn_at is not None

    # 4. Attempt to generate collection route -> Parcel MUST be excluded from dispatch
    plan_create = DeploymentPlanCreate(
        name="Consented Fleet Dispatch", date_start=date(2025, 10, 20), date_end=date(2025, 11, 15), region="Ludhiana"
    )

    # Either the plan contains other farms, or raises ValidationError if this was the only candidate
    try:
        plan = planner_svc.generate_deployment_plan(plan_create)
        assigned_farm_ids = [a.farm_id for a in plan.assignments]
        # Baddowal parcel must NOT be included
        assert farm.id not in assigned_farm_ids
    except Exception as e:
        # If no other farms exist in the window, it safely raises ValidationError
        assert "No unallocated biomass available" in str(e)

    # 5. Landholder submits Data Subject Request (DSR) for erasure / export
    # Create associated user for the farmer
    auth_svc = AuthService(db_session)
    user = auth_svc.register_user(
        UserRegisterRequest(
            username="harjit_kaur_farmer",
            email="harjit@punjabfarms.in",
            password="SecurePass@123",
            full_name="Harjit Kaur",
            role_name="FARMER",
            farmer_id=farmer.id,
        )
    )

    dsr = priv_svc.submit_subject_request(
        user_id=user.id, request_type="ERASURE", details={"reason": "Discontinued farming contract for 2026"}
    )
    assert dsr.id is not None
    assert dsr.status == "SUBMITTED"
    assert dsr.request_type == "ERASURE"
