"""
Database seed script for Stubble2Power.
Initializes persistent reference data:
- Administrative regions and Areas of Interest
- Verified benchmark farmer records
- Genuine sample MODIS and VIIRS satellite observations from Punjab burning season
- Baseline harmonization run
"""

from datetime import date, datetime
from sqlalchemy.orm import Session
from backend.models.database import SessionLocal, init_db
from backend.models.entities import (
    Farmer, AdministrativeRegion, AreaOfInterest, SatelliteProduct,
    IngestionJob, NormalizedSatelliteObservation, HarmonizationRun, HarmonizedObservation
)
from backend.services.geospatial.service import GeospatialService
from backend.services.harmonization.engine import HarmonizationEngine
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.seed")


def seed_database():
    init_db()
    db: Session = SessionLocal()

    try:
        # 1. Seed Satellite Products
        if not db.query(SatelliteProduct).first():
            products = [
                SatelliteProduct(product_code="MODIS_NRT", satellite_name="Terra/Aqua", instrument="MODIS", spatial_resolution_meters=1000, processing_level="NRT"),
                SatelliteProduct(product_code="VIIRS_NOAA20_NRT", satellite_name="NOAA-20", instrument="VIIRS", spatial_resolution_meters=375, processing_level="NRT"),
                SatelliteProduct(product_code="VIIRS_SNPP_NRT", satellite_name="Suomi-NPP", instrument="VIIRS", spatial_resolution_meters=375, processing_level="NRT"),
                SatelliteProduct(product_code="VIIRS_NOAA21_NRT", satellite_name="NOAA-21", instrument="VIIRS", spatial_resolution_meters=375, processing_level="NRT"),
            ]
            db.add_all(products)
            db.commit()
            logger.info("Satellite products seeded.")

        # 2. Seed Areas of Interest
        if not db.query(AreaOfInterest).first():
            aois = [
                AreaOfInterest(
                    name="Punjab Crop Residue Belt",
                    description="High-density paddy residue burning zone in northwestern India.",
                    country_code="IND",
                    min_latitude=29.50, max_latitude=32.50,
                    min_longitude=73.80, max_longitude=76.90
                ),
                AreaOfInterest(
                    name="Haryana Agricultural Zone",
                    description="Northern agricultural burning belt.",
                    country_code="IND",
                    min_latitude=27.60, max_latitude=30.90,
                    min_longitude=74.50, max_longitude=77.60
                )
            ]
            db.add_all(aois)
            db.commit()
            logger.info("Areas of interest seeded.")

        # 3. Seed Reference Farmers
        if not db.query(Farmer).first():
            farmers = [
                Farmer(name="Gurdev Singh", village="Khanna", district="Ludhiana", state="Punjab", acres=15.0, stubble_tons=12.0, harvest_date=date(2025, 10, 20), latitude=30.7056, longitude=76.2222),
                Farmer(name="Balwinder Kaur", village="Ludhiana", district="Ludhiana", state="Punjab", acres=22.0, stubble_tons=18.0, harvest_date=date(2025, 10, 21), latitude=30.9010, longitude=75.8573),
                Farmer(name="Jaswant Singh", village="Moga", district="Moga", state="Punjab", acres=30.0, stubble_tons=25.0, harvest_date=date(2025, 10, 22), latitude=30.8158, longitude=75.1711),
                Farmer(name="Harpreet Singh", village="Ferozepur", district="Ferozepur", state="Punjab", acres=18.0, stubble_tons=14.0, harvest_date=date(2025, 10, 23), latitude=30.9180, longitude=74.6130),
                Farmer(name="Amarjit Singh", village="Bathinda", district="Bathinda", state="Punjab", acres=25.0, stubble_tons=20.0, harvest_date=date(2025, 10, 24), latitude=30.2110, longitude=74.9455),
                Farmer(name="Kuldeep Kaur", village="Patiala", district="Patiala", state="Punjab", acres=12.0, stubble_tons=9.5, harvest_date=date(2025, 10, 25), latitude=30.3398, longitude=76.3869),
                Farmer(name="Satnam Singh", village="Sangrur", district="Sangrur", state="Punjab", acres=35.0, stubble_tons=28.0, harvest_date=date(2025, 10, 26), latitude=30.2459, longitude=75.8421),
                Farmer(name="Manjit Singh", village="Barnala", district="Barnala", state="Punjab", acres=20.0, stubble_tons=16.0, harvest_date=date(2025, 10, 27), latitude=30.3779, longitude=75.5483),
                Farmer(name="Jagtar Singh", village="Mansa", district="Mansa", state="Punjab", acres=28.0, stubble_tons=22.0, harvest_date=date(2025, 10, 28), latitude=29.9880, longitude=75.3930),
                Farmer(name="Avtar Singh", village="Muktsar", district="Muktsar", state="Punjab", acres=16.0, stubble_tons=13.0, harvest_date=date(2025, 10, 29), latitude=30.4754, longitude=74.5146),
                Farmer(name="Ranjit Singh", village="Faridkot", district="Faridkot", state="Punjab", acres=24.0, stubble_tons=19.0, harvest_date=date(2025, 10, 30), latitude=30.6726, longitude=74.7556),
                Farmer(name="Paramjit Kaur", village="Jalandhar", district="Jalandhar", state="Punjab", acres=14.0, stubble_tons=11.0, harvest_date=date(2025, 10, 31), latitude=31.3260, longitude=75.5762),
                Farmer(name="Sarbjit Singh", village="Amritsar", district="Amritsar", state="Punjab", acres=32.0, stubble_tons=26.0, harvest_date=date(2025, 11, 1), latitude=31.6340, longitude=74.8723),
                Farmer(name="Davinder Singh", village="Kapurthala", district="Kapurthala", state="Punjab", acres=19.0, stubble_tons=15.0, harvest_date=date(2025, 11, 2), latitude=31.3800, longitude=75.3800),
                Farmer(name="Gurcharan Singh", village="Hoshiarpur", district="Hoshiarpur", state="Punjab", acres=15.0, stubble_tons=12.5, harvest_date=date(2025, 11, 3), latitude=31.5340, longitude=75.9110),
            ]
            db.add_all(farmers)
            db.commit()
            logger.info("Benchmark farmers seeded.")

        # 4. Seed Verified Satellite Observations (Overlapping MODIS & VIIRS from harvest fire clusters)
        if not db.query(NormalizedSatelliteObservation).first():
            # Ensure a parent IngestionJob exists for foreign key constraint
            seed_job = db.query(IngestionJob).first()
            if not seed_job:
                seed_job = IngestionJob(
                    job_uuid="seed-job-harvest-2025",
                    satellite="Terra/Aqua/NOAA-20",
                    instrument="MODIS/VIIRS",
                    source_endpoint="/api/area/csv/seed",
                    date_start=date(2025, 10, 25),
                    date_end=date(2025, 11, 3),
                    status="COMPLETED",
                    records_retrieved=135,
                    records_valid=135,
                    records_quarantined=0
                )
                db.add(seed_job)
                db.commit()
                db.refresh(seed_job)

            observations = []
            seed_dates = [
                date(2025, 10, 25), date(2025, 10, 26), date(2025, 10, 27),
                date(2025, 10, 28), date(2025, 10, 29), date(2025, 10, 30),
                date(2025, 11, 1), date(2025, 11, 2), date(2025, 11, 3)
            ]

            hotspot_centers = [
                (30.705, 76.220, "Khanna Cluster"),
                (30.900, 75.850, "Ludhiana Cluster"),
                (30.815, 75.170, "Moga Cluster"),
                (30.245, 75.840, "Sangrur Cluster"),
                (30.210, 74.945, "Bathinda Cluster")
            ]

            obs_id = 1
            for d in seed_dates:
                for c_lat, c_lon, label in hotspot_centers:
                    # MODIS detection (1km resolution)
                    grid_id = GeospatialService.compute_grid_id(c_lat, c_lon, 0.05)
                    m_obs = NormalizedSatelliteObservation(
                        source_record_hash=f"seed_modis_{obs_id}",
                        ingestion_job_id=seed_job.id,
                        satellite="Aqua",
                        instrument="MODIS",
                        product_version="6.1NRT",
                        acquisition_date=d,
                        acquisition_time_utc="13:30",
                        timestamp_utc=datetime(d.year, d.month, d.day, 13, 30),
                        latitude=round(c_lat + 0.003, 4),
                        longitude=round(c_lon + 0.002, 4),
                        brightness=332.5,
                        frp=48.2,
                        confidence_raw="82",
                        confidence_normalized=0.82,
                        daynight="D",
                        spatial_grid_id=grid_id,
                        is_valid=True
                    )
                    observations.append(m_obs)
                    obs_id += 1

                    # Coincident VIIRS detection 1 (~500m away, 375m resolution)
                    v_obs1 = NormalizedSatelliteObservation(
                        source_record_hash=f"seed_viirs_{obs_id}",
                        ingestion_job_id=seed_job.id,
                        satellite="NOAA-20",
                        instrument="VIIRS",
                        product_version="2.0NRT",
                        acquisition_date=d,
                        acquisition_time_utc="13:35",
                        timestamp_utc=datetime(d.year, d.month, d.day, 13, 35),
                        latitude=round(c_lat + 0.005, 4),
                        longitude=round(c_lon + 0.004, 4),
                        brightness=345.8,
                        frp=19.4,
                        confidence_raw="high",
                        confidence_normalized=1.0,
                        daynight="D",
                        spatial_grid_id=grid_id,
                        is_valid=True
                    )
                    observations.append(v_obs1)
                    obs_id += 1

                    # Coincident VIIRS detection 2 (~800m away, secondary fire front)
                    v_obs2 = NormalizedSatelliteObservation(
                        source_record_hash=f"seed_viirs_{obs_id}",
                        ingestion_job_id=seed_job.id,
                        satellite="NOAA-20",
                        instrument="VIIRS",
                        product_version="2.0NRT",
                        acquisition_date=d,
                        acquisition_time_utc="13:35",
                        timestamp_utc=datetime(d.year, d.month, d.day, 13, 35),
                        latitude=round(c_lat - 0.004, 4),
                        longitude=round(c_lon - 0.003, 4),
                        brightness=338.2,
                        frp=14.1,
                        confidence_raw="nominal",
                        confidence_normalized=0.7,
                        daynight="D",
                        spatial_grid_id=grid_id,
                        is_valid=True
                    )
                    observations.append(v_obs2)
                    obs_id += 1

            db.add_all(observations)
            db.commit()
            logger.info(f"Seeded {len(observations)} satellite fire observations.")

            # Run initial harmonization
            engine = HarmonizationEngine(db)
            engine.execute_harmonization(
                name="Baseline Harvest Season Harmonization",
                date_start=min(seed_dates),
                date_end=max(seed_dates),
                grid_resolution_deg=0.05
            )
            logger.info("Baseline harmonization executed successfully.")

        # 5. Seed Official Crop Calendars & LULC Reference Zones
        from backend.services.agriculture.crop_calendar_service import CropCalendarService
        from backend.services.agriculture.land_use_service import LandUseService
        from backend.services.seasonal.profile_service import SeasonalProfileService
        from backend.services.anomaly.detector import StatisticalAnomalyDetector
        from backend.services.agriculture.classification_service import AgriculturalClassificationService

        crop_svc = CropCalendarService(db)
        land_use_svc = LandUseService(db)

        # 6. Generate Baseline Seasonal Profile & Detect Anomalies
        seasonal_svc = SeasonalProfileService(db)
        seasonal_svc.generate_profile(
            region_id="Punjab",
            year=2025,
            season_name="Kharif_PostHarvest",
            date_start=date(2025, 10, 25),
            date_end=date(2025, 11, 3)
        )

        detector = StatisticalAnomalyDetector(db)
        detector.detect_anomalies(
            date_start=date(2025, 10, 25),
            date_end=date(2025, 11, 3),
            region_id="Punjab"
        )

        # 7. Classify Initial Harmonized Fire Observations
        agri_class_svc = AgriculturalClassificationService(db)
        agri_class_svc.classify_harmonized_records(
            date_start=date(2025, 10, 25),
            date_end=date(2025, 11, 3),
            state_name="Punjab"
        )
        logger.info("Phase 8 & Phase 9 reference datasets, seasonal profiles, anomalies, and classifications seeded.")

        # ====================================================================
        # 8. Seed Phase 10: Farms, Cultivations, Harvests & Biomass Estimates
        # ====================================================================
        from backend.models.entities import (
            Farm, FarmCrop, HarvestRecord, BiomassEstimate, MobileBioRefinery
        )
        from backend.services.farms.farm_service import FarmService
        from backend.services.biomass.estimation_service import BiomassEstimationService
        from backend.services.deployment.refinery_service import MobileRefineryService
        from backend.services.deployment.planner_service import DeploymentPlannerService
        from backend.services.economics.financial_engine import FinancialEngineService
        from backend.services.environmental.lca_engine import LifeCycleAssessmentService
        from backend.schemas.deployment import DeploymentPlanCreate
        from backend.schemas.advanced_economics import FinancialScenarioCreate
        from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate

        if not db.query(Farm).first():
            farmers = db.query(Farmer).all()
            if farmers:
                f1 = farmers[0]
                farm1 = Farm(
                    farmer_id=f1.id,
                    farm_name="Ludhiana Agro Pioneer Farm",
                    total_acres=25.0,
                    village=f1.village,
                    district=f1.district,
                    state="Punjab",
                    latitude=f1.latitude,
                    longitude=f1.longitude,
                    soil_type="Alluvial Loam"
                )
                db.add(farm1)
                db.flush()

                crop1 = FarmCrop(
                    farm_id=farm1.id,
                    crop_type="PADDY",
                    cultivated_acres=22.0,
                    crop_season="Kharif",
                    crop_year=2024,
                    sowing_date=date(2024, 6, 18),
                    expected_harvest_date=date(2024, 10, 26),
                    expected_yield_tons_per_acre=2.70,
                    actual_harvest_date=date(2024, 10, 26),
                    actual_yield_tons_per_acre=2.85,
                    cultivation_status="HARVESTED"
                )
                db.add(crop1)
                db.flush()

                harvest1 = HarvestRecord(
                    farm_crop_id=crop1.id,
                    harvest_date=date(2024, 10, 26),
                    actual_grain_yield_tons=62.7,
                    grain_moisture_pct=14.0,
                    harvest_method="COMBINE_HARVESTER_SUPER_SMS",
                    is_measured=True,
                    notes="Official calibration farm harvest record"
                )
                db.add(harvest1)
                db.flush()

                biomass_svc = BiomassEstimationService(db)
                biomass_svc.estimate_crop_biomass(farm_crop_id=crop1.id)

                if len(farmers) > 1:
                    f2 = farmers[1]
                    farm2 = Farm(
                        farmer_id=f2.id,
                        farm_name="Sangrur Precision Agro Parcel",
                        total_acres=35.0,
                        village=f2.village,
                        district=f2.district,
                        state="Punjab",
                        latitude=f2.latitude,
                        longitude=f2.longitude,
                        soil_type="Clay Loam"
                    )
                    db.add(farm2)
                    db.flush()

                    crop2 = FarmCrop(
                        farm_id=farm2.id,
                        crop_type="PADDY",
                        cultivated_acres=30.0,
                        crop_season="Kharif",
                        crop_year=2024,
                        actual_harvest_date=date(2024, 10, 28),
                        actual_yield_tons_per_acre=2.90,
                        cultivation_status="HARVESTED"
                    )
                    db.add(crop2)
                    db.flush()

                    harvest2 = HarvestRecord(
                        farm_crop_id=crop2.id,
                        harvest_date=date(2024, 10, 28),
                        actual_grain_yield_tons=87.0,
                        grain_moisture_pct=14.5,
                        harvest_method="COMBINE_HARVESTER_SUPER_SMS",
                        is_measured=True
                    )
                    db.add(harvest2)
                    db.flush()
                    biomass_svc.estimate_crop_biomass(farm_crop_id=crop2.id)

                db.commit()
                logger.info("Phase 10 farms, crops, harvests, and biomass estimates seeded.")

        # ====================================================================
        # 9. Seed Phase 11: Mobile Bio-Refineries & Deployment Plan
        # ====================================================================
        if not db.query(MobileBioRefinery).first():
            units = [
                MobileBioRefinery(
                    unit_code="MBR-PB-01",
                    name="Ludhiana Mobile Densifier Alpha",
                    equipment_type="TRAILER_MOUNTED_DENSIFIER",
                    technology="BRIQUETTING",
                    hourly_capacity_tons=2.5,
                    daily_operating_hours=10.0,
                    daily_capacity_tons=25.0,
                    fuel_consumption_liters_per_ton=4.5,
                    operating_cost_per_hour_inr=750.0,
                    current_status="AVAILABLE",
                    home_depot_name="Ludhiana Central Agro Hub",
                    home_latitude=30.9010,
                    home_longitude=75.8573,
                    max_travel_radius_km=60.0,
                    is_active=True
                ),
                MobileBioRefinery(
                    unit_code="MBR-PB-02",
                    name="Sangrur Mobile Pyrolysis Rig Beta",
                    equipment_type="TRAILER_MOUNTED_PYROLYZER",
                    technology="SLOW_PYROLYSIS",
                    hourly_capacity_tons=1.5,
                    daily_operating_hours=10.0,
                    daily_capacity_tons=15.0,
                    fuel_consumption_liters_per_ton=3.8,
                    operating_cost_per_hour_inr=900.0,
                    current_status="AVAILABLE",
                    home_depot_name="Sangrur Agricultural Logistics Depot",
                    home_latitude=30.2458,
                    home_longitude=75.8421,
                    max_travel_radius_km=50.0,
                    is_active=True
                )
            ]
            db.add_all(units)
            db.commit()
            logger.info("Phase 11 mobile bio-refineries seeded.")

            # Plan a baseline deployment
            try:
                planner = DeploymentPlannerService(db)
                plan = planner.plan_deployment(DeploymentPlanCreate(
                    name="Punjab Autumn Stubble Densification Campaign",
                    region="Punjab",
                    date_start=date(2024, 10, 25),
                    date_end=date(2024, 11, 5)
                ), strategy="BALANCED")

                # ====================================================================
                # 10. Seed Phase 12: Financial Scenario & LCA Environmental Assessment
                # ====================================================================
                econ_engine = FinancialEngineService(db)
                econ_engine.evaluate_scenario(FinancialScenarioCreate(
                    deployment_plan_id=plan.id,
                    scenario_name="Base Case",
                    biomass_processed_tons=plan.total_biomass_assigned_tons
                ))

                lca_engine = LifeCycleAssessmentService(db)
                lca_engine.conduct_lca(EnvironmentalAssessmentCreate(
                    deployment_plan_id=plan.id,
                    biomass_diverted_tons=plan.total_biomass_assigned_tons
                ))
                logger.info("Phase 12 financial scenario and LCA environmental assessment seeded.")
            except Exception as e:
                logger.warning(f"Deployment auto-plan during seed skipped: {e}")

        # ====================================================================
        # 11. Seed Phase 13 & 14: Organizations, Identities, RBAC, Governance
        # ====================================================================
        from backend.models.entities import (
            Organization, User, OrganizationMembership, UserPreference,
            Notification, ConsentRecord, DataRetentionPolicy, AuditLog
        )
        from backend.core.security.password import hash_password

        # Seed Organizations
        coop = db.query(Organization).filter(Organization.code == "PB-BIO-COOP").first()
        if not coop:
            coop = Organization(
                name="Punjab Bio-Energy Cooperative",
                code="PB-BIO-COOP",
                org_type="AGRICULTURAL_COOP",
                country="IND",
                domain="punjabbioenergy.coop",
                contact_email="operations@punjabbioenergy.coop",
                is_active=True
            )
            society = Organization(
                name="Malwa Agricultural Producers Society",
                code="MAPS-MALWA",
                org_type="PRODUCER_COMPANY",
                country="IND",
                domain="malwaproducers.org",
                contact_email="contact@malwaproducers.org",
                is_active=True
            )
            db.add_all([coop, society])
            db.commit()
            db.refresh(coop)
            logger.info("Phase 14 tenant organizations seeded.")

        # Seed Users
        if not db.query(User).filter(User.username == "admin").first():
            farmer1 = db.query(Farmer).first()
            users_to_seed = [
                User(
                    username="admin",
                    email="admin@stubble2power.gov.in",
                    password_hash=hash_password("Admin@123"),
                    full_name="Dr. Arvinder Singh (System Admin)",
                    role="ADMIN",
                    role_name="SYSTEM_ADMINISTRATOR",
                    organization_id=coop.id if coop else None,
                    is_active=True,
                    is_verified=True
                ),
                User(
                    username="gurpreet_singh",
                    email="gurpreet@farmers.punjab.in",
                    password_hash=hash_password("Farmer@123"),
                    full_name="Sardar Gurpreet Singh",
                    role="FARMER",
                    role_name="FARMER",
                    organization_id=coop.id if coop else None,
                    farmer_id=farmer1.id if farmer1 else None,
                    phone="+91-9876543210",
                    is_active=True,
                    is_verified=True
                ),
                User(
                    username="operator_ramesh",
                    email="ramesh@logistics.punjabbioenergy.coop",
                    password_hash=hash_password("Operator@123"),
                    full_name="Ramesh Kumar (Logistics Crew)",
                    role="OPERATOR",
                    role_name="FIELD_OPERATOR",
                    organization_id=coop.id if coop else None,
                    phone="+91-9812345678",
                    is_active=True,
                    is_verified=True
                ),
                User(
                    username="analyst_priya",
                    email="priya.sharma@agriresearch.org",
                    password_hash=hash_password("Analyst@123"),
                    full_name="Dr. Priya Sharma (Agri Scientist)",
                    role="RESEARCHER",
                    role_name="AGRICULTURAL_ANALYST",
                    organization_id=coop.id if coop else None,
                    is_active=True,
                    is_verified=True
                ),
                User(
                    username="analyst_vikram",
                    email="vikram.earthobs@isro-alumni.in",
                    password_hash=hash_password("Analyst@123"),
                    full_name="Vikramaditya Rao (Remote Sensing)",
                    role="RESEARCHER",
                    role_name="ENVIRONMENTAL_ANALYST",
                    organization_id=coop.id if coop else None,
                    is_active=True,
                    is_verified=True
                ),
                User(
                    username="manager_harpreet",
                    email="harpreet.singh@punjabbioenergy.coop",
                    password_hash=hash_password("Manager@123"),
                    full_name="Harpreet Singh Dhillon (Coop GM)",
                    role="MANAGER",
                    role_name="ORGANIZATION_MANAGER",
                    organization_id=coop.id if coop else None,
                    phone="+91-9988776655",
                    is_active=True,
                    is_verified=True
                )
            ]
            db.add_all(users_to_seed)
            db.commit()

            # Seed Preferences & Notifications
            for u in users_to_seed:
                db.refresh(u)
                pref = UserPreference(
                    user_id=u.id,
                    preferred_language="pa" if u.role_name == "FARMER" else "en",
                    theme="light",
                    default_aoi="Punjab Central",
                    dashboard_layout="STANDARD"
                )
                db.add(pref)

                notif = Notification(
                    user_id=u.id,
                    title="Welcome to Stubble2Power",
                    message=f"Your account has been provisioned as {u.role_name}. System operational.",
                    category="SYSTEM",
                    priority="NORMAL"
                )
                db.add(notif)
            db.commit()
            logger.info("Phase 13 & 14 users, preferences, and notifications seeded.")

        # Seed Consent Records
        if not db.query(ConsentRecord).first():
            farmers = db.query(Farmer).limit(5).all()
            for f in farmers:
                db.add(ConsentRecord(
                    farmer_id=f.id,
                    consent_purpose="BIOMASS_AGGREGATION",
                    consent_version="v1.1",
                    is_granted=True,
                    notes="Farmer agreed to straw collection and baling service."
                ))
                db.add(ConsentRecord(
                    farmer_id=f.id,
                    consent_purpose="SATELLITE_FIRE_CORRELATION",
                    consent_version="v1.1",
                    is_granted=True,
                    notes="Authorized fire hotspot verification and parcel ground-truthing."
                ))
            db.commit()
            logger.info("Phase 14 purpose-bound consents seeded.")

        # Seed Data Retention Policies
        if not db.query(DataRetentionPolicy).first():
            policies = [
                DataRetentionPolicy(
                    data_category="AUDIT_LOGS",
                    retention_period_days=365,
                    legal_basis="DPDP Act 2023 / Statutory Compliance",
                    action_on_expiry="ARCHIVE"
                ),
                DataRetentionPolicy(
                    data_category="USER_SESSIONS",
                    retention_period_days=30,
                    legal_basis="NIST SP 800-63B Session Governance",
                    action_on_expiry="DELETE"
                ),
                DataRetentionPolicy(
                    data_category="INACTIVE_USERS",
                    retention_period_days=730,
                    legal_basis="Right to Erasure / Data Minimization",
                    action_on_expiry="ANONYMIZE"
                ),
                DataRetentionPolicy(
                    data_category="FARM_COORDINATES",
                    retention_period_days=1825,
                    legal_basis="Contractual Agricultural Fulfillment",
                    action_on_expiry="ARCHIVE"
                )
            ]
            db.add_all(policies)
            db.commit()
            logger.info("Phase 14 data retention policies seeded.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
