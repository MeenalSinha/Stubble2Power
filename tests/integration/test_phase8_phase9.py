"""
Integration Tests for Phase 8 and Phase 9 End-to-End Pipeline & API Handlers.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.models.entities import HarmonizationRun, HarmonizedObservation
from backend.api.routes.seasonal import get_seasonal_profiles, generate_seasonal_profile, get_historical_baselines
from backend.api.routes.anomalies import get_anomalies, detect_anomalies
from backend.api.routes.agriculture import get_crop_calendars, classify_fire_activity, get_agricultural_summary
from backend.schemas.seasonal import SeasonalProfileCreate
from backend.schemas.anomaly import AnomalyDetectRequest
from backend.schemas.agriculture import AgriculturalClassificationRequest


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestPhase8Phase9Integration:
    def test_full_pipeline_harmonization_to_agriculture(self, test_db):
        # 1. Seed Harmonization Run & Observations
        run = HarmonizationRun(
            run_uuid="phase89-integration-run",
            name="Phase 8 & 9 Integration Run",
            date_start=date(2025, 10, 20),
            date_end=date(2025, 11, 10),
            grid_resolution_deg=0.05
        )
        test_db.add(run)
        test_db.commit()

        # Seed 10 daily harmonized observations in Punjab agricultural heartland
        for i in range(10):
            d = date(2025, 10, 25) + timedelta(days=i)
            # Normal burning around 25 MW, one high spike of 160 MW on day 5 (Nov 01)
            frp = 160.0 if i == 5 else 25.0
            obs = HarmonizedObservation(
                harmonization_run_id=run.id,
                grid_id=f"GRID_PB_{i}",
                observation_date=d,
                centroid_lat=30.85 + (i * 0.01),
                centroid_lon=75.50 + (i * 0.01),
                modis_count=2,
                viirs_count=3,
                total_detections=5,
                harmonized_frp_mw=frp,
                harmonized_activity_index=frp / 2.0,
                consensus_score=0.95
            )
            test_db.add(obs)
        test_db.commit()

        # 2. Test Seasonal Profile Generation API Route Handler
        profile_req = SeasonalProfileCreate(
            region_id="Punjab",
            year=2025,
            season_name="Kharif_PostHarvest",
            date_start=date(2025, 10, 20),
            date_end=date(2025, 11, 10)
        )
        profile_res = generate_seasonal_profile(payload=profile_req, db=test_db)
        assert profile_res.year == 2025
        assert profile_res.total_activity > 0.0
        assert profile_res.peak_date is not None

        # Verify listing seasonal profiles
        profiles_list = get_seasonal_profiles(region_id="Punjab", db=test_db)
        assert len(profiles_list) >= 1

        # 3. Test Anomaly Detection API Route Handler
        anomaly_req = AnomalyDetectRequest(
            region_id="Punjab",
            date_start=date(2025, 10, 25),
            date_end=date(2025, 11, 5)
        )
        anomaly_summary = detect_anomalies(payload=anomaly_req, db=test_db)
        assert anomaly_summary.total_anomalies >= 1
        # The 160 MW spike on Day 5 must be detected
        spike_found = any(a.observed_activity == 160.0 for a in anomaly_summary.anomalies)
        assert spike_found is True

        # Verify listing anomalies
        anom_list = get_anomalies(region_id="Punjab", db=test_db)
        assert len(anom_list) >= 1

        # 4. Test Crop Calendars Route Handler
        calendars = get_crop_calendars(state_name="Punjab", db=test_db)
        assert len(calendars) >= 4
        crop_names = [c.crop_name for c in calendars]
        assert any("Paddy" in name for name in crop_names)

        # 5. Test Agricultural Classification Route Handler
        class_req = AgriculturalClassificationRequest(
            date_start=date(2025, 10, 25),
            date_end=date(2025, 11, 5),
            state_name="Punjab"
        )
        classified_records = classify_fire_activity(payload=class_req, db=test_db)
        assert len(classified_records) == 10
        # Check that central Punjab fires during Oct/Nov are classified as LIKELY_AGRICULTURAL_CONTEXT
        likely_fires = [r for r in classified_records if r.context_classification == "LIKELY_AGRICULTURAL_CONTEXT"]
        assert len(likely_fires) >= 8

        # 6. Test Agricultural Summary Route Handler
        summary = get_agricultural_summary(date_start=date(2025, 10, 25), date_end=date(2025, 11, 5), db=test_db)
        assert summary.total_assessed == 10
        assert summary.likely_agricultural_count >= 8
        assert summary.percent_likely_agricultural > 70.0
        assert "Paddy / Rice (Kharif)" in summary.crop_breakdown
