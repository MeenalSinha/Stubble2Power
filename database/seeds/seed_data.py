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

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
