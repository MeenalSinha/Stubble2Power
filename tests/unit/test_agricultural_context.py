"""
Unit Tests for Phase 9: Agricultural Reference Data, Crop Calendars, and Context Classification.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.services.agriculture.crop_calendar_service import CropCalendarService
from backend.services.agriculture.land_use_service import LandUseService
from backend.services.agriculture.classification_service import AgriculturalClassificationService


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestCropCalendarService:
    def test_calendar_seeding_and_harvest_matching(self, in_memory_db):
        svc = CropCalendarService(in_memory_db)
        calendars = svc.get_all_calendars(state_name="Punjab")
        assert len(calendars) >= 4

        # Oct 25: Peak Kharif Paddy burn window in Punjab
        match_peak = svc.match_harvest_window(date(2025, 10, 25), state_name="Punjab")
        assert match_peak["status"] == "IN_PEAK_HARVEST_WINDOW"
        assert "Paddy" in match_peak["matched_crop"]
        assert match_peak["susceptibility"] == "HIGH"

        # Dec 05: Extended harvest window for Cotton / Late Paddy
        match_ext = svc.match_harvest_window(date(2025, 12, 5), state_name="Punjab")
        assert match_ext["status"] in ("IN_EXTENDED_HARVEST_WINDOW", "IN_PEAK_HARVEST_WINDOW")

        # Jul 10: Off-season for harvesting/burning (sowing period)
        match_off = svc.match_harvest_window(date(2025, 7, 10), state_name="Punjab")
        assert match_off["status"] == "OFF_SEASON"


class TestLandUseService:
    def test_land_use_classification(self, in_memory_db):
        svc = LandUseService(in_memory_db)

        # Ludhiana Rural Farm (Cropland)
        lu_farm = svc.classify_coordinate(30.8, 75.5)
        assert lu_farm["land_use_class"] == "CROPLAND"
        assert lu_farm["distance_to_cropland_km"] == 0.0
        assert lu_farm["confidence"] >= 0.85

        # Shivalik Foothills (Forest)
        lu_forest = svc.classify_coordinate(31.8, 76.4)
        assert lu_forest["land_use_class"] == "FOREST"
        assert lu_forest["distance_to_cropland_km"] > 0.0

        # Ludhiana Focal Point Industrial Zone (Urban/Industrial)
        lu_urban = svc.classify_coordinate(30.90, 75.88)
        assert lu_urban["land_use_class"] == "URBAN_INDUSTRIAL"


class TestAgriculturalClassificationService:
    def test_likely_agricultural_classification(self, in_memory_db):
        svc = AgriculturalClassificationService(in_memory_db)
        # Point in central Punjab cropland on Nov 02 during peak harvest with moderate FRP 45 MW
        assessment = svc.assess_observation(
            observation_date=date(2025, 11, 2), latitude=30.8, longitude=75.5, grid_id="GRID_PB_LUDHIANA", frp_mw=45.0
        )
        assert assessment.context_classification == "LIKELY_AGRICULTURAL_CONTEXT"
        assert assessment.confidence_score >= 0.70
        assert assessment.matched_crop is not None
        assert assessment.harvest_window_status == "IN_PEAK_HARVEST_WINDOW"
        assert assessment.stubble_risk_index > 70.0
        assert "evidence_factors" in assessment.evidence_json

    def test_other_land_use_forest_fire(self, in_memory_db):
        svc = AgriculturalClassificationService(in_memory_db)
        # Point in Shivalik forest reserve during April with high FRP
        assessment = svc.assess_observation(
            observation_date=date(2025, 4, 15),
            latitude=31.8,
            longitude=76.4,
            grid_id="GRID_SHIVALIK_FOREST",
            frp_mw=80.0,
        )
        assert assessment.context_classification == "OTHER_LAND_USE_CONTEXT"
        assert assessment.land_use_class == "FOREST"
        assert assessment.stubble_risk_index == 0.0

    def test_other_land_use_excessive_frp_industrial(self, in_memory_db):
        svc = AgriculturalClassificationService(in_memory_db)
        # FRP of 650 MW exceeds empirical crop residue combustion upper limit (250 MW)
        assessment = svc.assess_observation(
            observation_date=date(2025, 11, 2),
            latitude=30.8,
            longitude=75.5,
            grid_id="GRID_INDUSTRIAL_BLAST",
            frp_mw=650.0,
        )
        assert assessment.context_classification == "OTHER_LAND_USE_CONTEXT"
        assert "exceeds typical crop residue limit" in assessment.evidence_json["evidence_factors"][-1]

    def test_architectural_separation_rule_verified(self, in_memory_db):
        """
        Verify that classification does NOT accept or require any Phase 8 statistical anomaly input.
        Anomalous fire activity does NOT imply agricultural context.
        """
        svc = AgriculturalClassificationService(in_memory_db)
        import inspect

        sig = inspect.signature(svc.assess_observation)
        # Assert parameters do not contain anomaly_score or z_score
        assert "anomaly_score" not in sig.parameters
        assert "z_score" not in sig.parameters
        assert "is_anomaly" not in sig.parameters
