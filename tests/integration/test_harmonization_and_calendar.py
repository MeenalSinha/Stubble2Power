"""
Integration tests for Scientific Harmonization and Activity Calendar engines.
"""

import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base
from backend.models.entities import NormalizedSatelliteObservation
from backend.services.harmonization.engine import HarmonizationEngine
from backend.services.calendar.service import CalendarAggregationService


@pytest.fixture
def populated_sat_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    obs_date = date(2025, 10, 25)

    # 1. MODIS observation (Terra, 10:30 UTC)
    obs_modis = NormalizedSatelliteObservation(
        source_record_hash="hash_modis_1",
        ingestion_job_id=1,
        satellite="Terra",
        instrument="MODIS",
        product_version="6.1NRT",
        acquisition_date=obs_date,
        acquisition_time_utc="10:30",
        timestamp_utc=datetime(2025, 10, 25, 10, 30),
        latitude=30.850,
        longitude=75.400,
        brightness=325.0,
        frp=55.0,
        confidence_raw="80",
        confidence_normalized=0.80,
        daynight="D",
        spatial_grid_id="grid_30.8500_75.4000",
        is_valid=True
    )

    # 2. VIIRS observation (NOAA-20, 10:45 UTC, ~1km away)
    obs_viirs_1 = NormalizedSatelliteObservation(
        source_record_hash="hash_viirs_1",
        ingestion_job_id=1,
        satellite="NOAA-20",
        instrument="VIIRS",
        product_version="2.0NRT",
        acquisition_date=obs_date,
        acquisition_time_utc="10:45",
        timestamp_utc=datetime(2025, 10, 25, 10, 45),
        latitude=30.855,
        longitude=75.405,
        brightness=338.0,
        frp=20.0,
        confidence_raw="nominal",
        confidence_normalized=0.70,
        daynight="D",
        spatial_grid_id="grid_30.8500_75.4000",
        is_valid=True
    )

    # 3. Another VIIRS observation in same cluster (~700m away)
    obs_viirs_2 = NormalizedSatelliteObservation(
        source_record_hash="hash_viirs_2",
        ingestion_job_id=1,
        satellite="NOAA-20",
        instrument="VIIRS",
        product_version="2.0NRT",
        acquisition_date=obs_date,
        acquisition_time_utc="10:45",
        timestamp_utc=datetime(2025, 10, 25, 10, 45),
        latitude=30.853,
        longitude=75.402,
        brightness=342.0,
        frp=15.0,
        confidence_raw="high",
        confidence_normalized=1.00,
        daynight="D",
        spatial_grid_id="grid_30.8500_75.4000",
        is_valid=True
    )

    session.add_all([obs_modis, obs_viirs_1, obs_viirs_2])
    session.commit()

    try:
        yield session
    finally:
        session.close()


class TestHarmonizationAndCalendar:
    def test_harmonization_run_and_association(self, populated_sat_db):
        engine = HarmonizationEngine(populated_sat_db)

        run = engine.execute_harmonization(
            name="Test Harmonization Run",
            date_start=date(2025, 10, 24),
            date_end=date(2025, 10, 26),
            grid_resolution_deg=0.05
        )

        assert run.status == "COMPLETED"
        assert run.total_input_observations == 3
        assert run.harmonized_cells_count == 1
        assert run.associated_pairs_count >= 1
        assert run.mean_consensus_score >= 0.70

    def test_calendar_daily_and_monthly(self, populated_sat_db):
        engine = HarmonizationEngine(populated_sat_db)
        engine.execute_harmonization(date_start=date(2025, 10, 24), date_end=date(2025, 10, 26))

        cal_svc = CalendarAggregationService(populated_sat_db)

        # Daily calendar
        daily = cal_svc.get_daily_calendar(date(2025, 10, 24), date(2025, 10, 26))
        assert len(daily) == 3

        # Oct 25 has detections
        oct25 = next(d for d in daily if d.date == date(2025, 10, 25))
        assert oct25.total_detections == 3
        assert oct25.modis_detections == 1
        assert oct25.viirs_detections == 2
        assert oct25.coverage_status == "COMPLETE"
        assert oct25.harmonized_activity_index > 0

        # Oct 24 has no detections
        oct24 = next(d for d in daily if d.date == date(2025, 10, 24))
        assert oct24.total_detections == 0
        assert oct24.coverage_status in ["NO_OVERPASS", "ZERO_BURNING"]
