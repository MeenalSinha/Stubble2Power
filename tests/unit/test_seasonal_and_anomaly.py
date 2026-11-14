"""
Unit Tests for Phase 8: Seasonal Baselines, Profiles, and Statistical Anomaly Detection.
"""

import pytest
from datetime import date, timedelta
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.models.entities import HarmonizedObservation, HarmonizationRun
from backend.services.seasonal.baseline_service import HistoricalBaselineService
from backend.services.seasonal.profile_service import SeasonalProfileService
from backend.services.anomaly.detector import StatisticalAnomalyDetector
from backend.services.anomaly.explanation_service import AnomalyExplanationService


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestSeasonalBaselineService:
    def test_compute_baseline_sufficient_history(self, in_memory_db):
        svc = HistoricalBaselineService(in_memory_db)
        # Generate 4 years of observations for a specific day of year (e.g. Day 300)
        daily_records = [
            {"date": "2022-10-27", "harmonized_frp_mw": 30.0},
            {"date": "2023-10-27", "harmonized_frp_mw": 35.0},
            {"date": "2024-10-27", "harmonized_frp_mw": 32.0},
            {"date": "2025-10-27", "harmonized_frp_mw": 40.0},
        ]
        baselines = svc.compute_baselines_from_data(
            daily_records=daily_records,
            region_id="Punjab",
            analysis_period="TEST_MULTIYEAR",
            metric_type="harmonized_frp_mw",
        )
        assert len(baselines) == 1
        b = baselines[0]
        assert b.sample_count == 4
        assert b.mean_val == pytest.approx(34.25, 0.1)
        assert b.median_val == pytest.approx(33.5, 0.1)
        assert b.mad_val > 0.0
        assert b.data_sufficiency_status == "SUFFICIENT"

    def test_compute_baseline_limited_history(self, in_memory_db):
        svc = HistoricalBaselineService(in_memory_db)
        # Only 1 sample: should flag LIMITED_HISTORY (< min 3 periods)
        daily_records = [{"date": "2025-10-27", "harmonized_frp_mw": 25.0}]
        baselines = svc.compute_baselines_from_data(
            daily_records=daily_records,
            region_id="Punjab",
            analysis_period="TEST_LIMITED",
            metric_type="harmonized_frp_mw",
        )
        assert len(baselines) == 1
        assert baselines[0].data_sufficiency_status == "LIMITED_HISTORY"

    def test_robust_mad_on_extreme_outlier(self, in_memory_db):
        svc = HistoricalBaselineService(in_memory_db)
        # Normal observations around 20 MW with one massive outlier spike 500 MW
        daily_records = [
            {"date": "2021-10-20", "harmonized_frp_mw": 19.0},
            {"date": "2022-10-20", "harmonized_frp_mw": 20.0},
            {"date": "2023-10-20", "harmonized_frp_mw": 21.0},
            {"date": "2024-10-20", "harmonized_frp_mw": 22.0},
            {"date": "2025-10-20", "harmonized_frp_mw": 500.0},
        ]
        baselines = svc.compute_baselines_from_data(
            daily_records=daily_records,
            region_id="Punjab",
            analysis_period="TEST_OUTLIER",
            metric_type="harmonized_frp_mw",
        )
        b = baselines[0]
        # Median is resistant to the 500 outlier: median should stay around 21
        assert b.median_val == pytest.approx(21.0, 0.5)
        # Mean is dragged up by outlier
        assert b.mean_val > 100.0
        # MAD should be small, reflecting typical spread around median
        assert b.mad_val < 10.0


class TestSeasonalProfileService:
    def test_generate_seasonal_profile_curve_and_metrics(self, in_memory_db):
        # Create a harmonization run
        run = HarmonizationRun(
            run_uuid="test-run-seasonal",
            name="Test Seasonal Run",
            date_start=date(2025, 10, 1),
            date_end=date(2025, 11, 30),
            grid_resolution_deg=0.05,
        )
        in_memory_db.add(run)
        in_memory_db.commit()

        # Create bell-shaped harmonized observations peaking on 2025-11-05
        for day_offset in range(30):
            obs_d = date(2025, 10, 15) + timedelta(days=day_offset)
            # Gaussian bell curve centered on day 21 (Nov 5)
            frp = float(100.0 * np.exp(-0.5 * ((day_offset - 21) / 4.0) ** 2))
            obs = HarmonizedObservation(
                harmonization_run_id=run.id,
                grid_id=f"GRID_{day_offset}",
                observation_date=obs_d,
                centroid_lat=30.5,
                centroid_lon=75.5,
                harmonized_frp_mw=frp,
                harmonized_activity_index=frp / 2.0,
            )
            in_memory_db.add(obs)
        in_memory_db.commit()

        svc = SeasonalProfileService(in_memory_db)
        profile = svc.generate_profile(
            region_id="Punjab",
            year=2025,
            season_name="Kharif_PostHarvest",
            date_start=date(2025, 10, 15),
            date_end=date(2025, 11, 15),
        )
        assert profile.year == 2025
        assert profile.total_activity > 0.0
        assert profile.peak_date == date(2025, 11, 5)
        assert profile.onset_date is not None
        assert profile.decay_date is not None
        assert "dates" in profile.profile_curve_json
        assert len(profile.profile_curve_json["daily_activity"]) == 32


class TestStatisticalAnomalyDetector:
    def test_detect_spike_anomaly(self, in_memory_db):
        run = HarmonizationRun(
            run_uuid="test-run-anomaly",
            name="Test Anomaly Run",
            date_start=date(2025, 10, 1),
            date_end=date(2025, 11, 10),
            grid_resolution_deg=0.05,
        )
        in_memory_db.add(run)
        in_memory_db.commit()

        # Seed baseline in db
        from backend.models.entities import HistoricalBaseline

        b = HistoricalBaseline(
            region_id="Punjab",
            analysis_period="OCT_NOV_MULTIYEAR",
            metric_type="harmonized_frp_mw",
            day_of_year=300,
            mean_val=20.0,
            median_val=18.0,
            std_val=6.0,
            mad_val=5.0,
            sample_count=5,
            data_sufficiency_status="SUFFICIENT",
        )
        in_memory_db.add(b)

        # Seed an extreme spike observation (120 MW vs 18 MW baseline -> MAD > 20)
        spike_obs = HarmonizedObservation(
            harmonization_run_id=run.id,
            grid_id="GRID_SPIKE_01",
            observation_date=date(2025, 10, 27),
            centroid_lat=30.9,
            centroid_lon=75.8,
            harmonized_frp_mw=120.0,
            harmonized_activity_index=85.0,
        )
        in_memory_db.add(spike_obs)
        in_memory_db.commit()

        detector = StatisticalAnomalyDetector(in_memory_db)
        anomalies = detector.detect_anomalies(
            date_start=date(2025, 10, 26), date_end=date(2025, 10, 28), region_id="Punjab"
        )
        assert len(anomalies) >= 1
        anom = anomalies[0]
        assert anom.grid_id == "GRID_SPIKE_01"
        assert anom.observed_activity == 120.0
        assert anom.mad_score > 3.0
        assert anom.severity_level in ("HIGH", "CRITICAL")
        assert anom.data_sufficiency_flag == "SUFFICIENT"
        assert "summary" in anom.explanation_json

    def test_explanation_service_structure(self):
        exp = AnomalyExplanationService.generate_explanation(
            observation_date=date(2025, 11, 4),
            grid_id="GRID_TEST_99",
            region_id="Punjab",
            observed_val=150.0,
            baseline_val=25.0,
            metric_name="Harmonized FRP (MW)",
            z_score=4.2,
            mad_score=5.1,
            anomaly_type="SPIKE",
            severity_level="CRITICAL",
            data_sufficiency_status="SUFFICIENT",
            co_occurring_count=3,
        )
        assert exp["severity_level"] == "CRITICAL"
        assert exp["anomaly_type"] == "SPIKE"
        assert "CRITICAL" in exp["statistical_evidence"]
        assert "+500.0%" in exp["summary"]
        assert "High confidence" in exp["data_sufficiency_reason"]
