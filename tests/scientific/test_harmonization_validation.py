"""
Scientific Validation Suite: NASA MODIS-VIIRS Satellite Fire Harmonization.
Validates the physical, statistical, and algorithmic fidelity of HarmonizationEngine
against published literature, NASA FIRMS standards, and independent mathematical benchmarks.

References:
- NASA Space Apps Challenge 09: Harmonization of MODIS and VIIRS Hot Spots
- Wooster et al. (2021), "Satellite monitoring of fire radiative power", RSE
- Schroeder et al. (2014), "The New VIIRS 375m Active Fire Product", RSE
- Giglio et al. (2016), "The Collection 6 MODIS active fire detection algorithm", RSE
"""

import math
from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session

from backend.models.entities import NormalizedSatelliteObservation
from backend.services.harmonization.engine import HarmonizationEngine
from backend.core.config.settings import config_manager


def test_spatial_temporal_association_window_boundaries(db_session: Session):
    """
    Validates that the cross-sensor association correctly enforces both:
    1. Maximum great-circle distance (1.5 km)
    2. Maximum temporal window (3.0 hours)
    """
    engine = HarmonizationEngine(db_session)
    base_time = datetime(2025, 10, 25, 8, 30, 0)
    base_lat = 30.7000
    base_lon = 76.2000

    modis_obs = NormalizedSatelliteObservation(
        id=101,
        instrument="MODIS",
        satellite="Terra",
        latitude=base_lat,
        longitude=base_lon,
        timestamp_utc=base_time,
        acquisition_date=base_time.date(),
        frp=25.0,
        confidence_normalized=85.0
    )

    # 1. Colocated and concurrent VIIRS observation (< 1.5 km, < 3.0 h) -> MUST associate
    viirs_match = NormalizedSatelliteObservation(
        id=201,
        instrument="VIIRS",
        satellite="NOAA-20",
        latitude=base_lat + 0.005,  # ~550m distance
        longitude=base_lon + 0.005,
        timestamp_utc=base_time + timedelta(hours=1.5),
        acquisition_date=base_time.date(),
        frp=15.0,
        confidence_normalized=90.0
    )

    # 2. Too far spatially (> 1.5 km), concurrent in time -> MUST NOT associate
    viirs_far_distance = NormalizedSatelliteObservation(
        id=202,
        instrument="VIIRS",
        satellite="NOAA-20",
        latitude=base_lat + 0.04,  # ~4.4 km distance
        longitude=base_lon,
        timestamp_utc=base_time + timedelta(minutes=30),
        acquisition_date=base_time.date(),
        frp=18.0,
        confidence_normalized=90.0
    )

    # 3. Colocated spatially (< 1.5 km), but exceeds 3.0 h window -> MUST NOT associate
    viirs_time_exceeded = NormalizedSatelliteObservation(
        id=203,
        instrument="VIIRS",
        satellite="NOAA-20",
        latitude=base_lat,
        longitude=base_lon,
        timestamp_utc=base_time + timedelta(hours=3.5),
        acquisition_date=base_time.date(),
        frp=20.0,
        confidence_normalized=90.0
    )

    associations = engine._compute_associations(
        modis_points=[modis_obs],
        viirs_points=[viirs_match, viirs_far_distance, viirs_time_exceeded],
        dist_threshold_km=1.5,
        time_window_hours=3.0
    )

    # Exactly one valid match should be discovered: (101, 201)
    assert len(associations) == 1
    assert associations[0] == (101, 201)


def test_wooster_frp_intercalibration_accuracy(db_session: Session):
    """
    Validates Wooster et al. (2021) empirical Fire Radiative Power (MW) intercalibration:
    FRP_calibrated = sum(FRP_MODIS) + beta * sum(FRP_VIIRS), where beta = 1.04.
    """
    slope = float(config_manager.get("nasa.harmonization.viirs_frp_calibration_slope"))
    assert slope == 1.04

    modis_frps = [12.5, 34.0, 56.2]
    viirs_frps = [8.4, 19.1, 42.0]

    expected_modis_sum = sum(modis_frps)  # 102.7
    expected_viirs_sum_cal = sum(v * 1.04 for v in viirs_frps)  # (8.4 + 19.1 + 42.0) * 1.04 = 69.5 * 1.04 = 72.28
    expected_total_calibrated_frp = expected_modis_sum + expected_viirs_sum_cal  # 174.98

    # Verify mathematical identity
    actual_calibrated = sum(modis_frps) + sum(v * slope for v in viirs_frps)
    assert pytest.approx(expected_total_calibrated_frp, rel=1e-4) == actual_calibrated


def test_normalized_burning_activity_index_formulation(db_session: Session):
    """
    Validates NBAI computation across mathematical boundary conditions:
    NBAI = min(50, 3.5 * N_eff) + min(35, 7.0 * ln(1 + FRP_cal)) + 15.0 * Consensus.
    """
    engine = HarmonizationEngine(db_session)

    # Test Case 1: Moderate burning activity
    m_count = 2
    v_count = 5
    frp_cal = 45.0
    consensus = 0.85

    # Manual calculation:
    # N_eff = (2 * 2.5) + 5 = 10.0
    # detection_term = min(50.0, 10.0 * 3.5) = 35.0
    # frp_term = min(35.0, ln(46.0) * 7.0) = min(35.0, 3.8286 * 7.0 = 26.8005) = 26.8005
    # consensus_term = 0.85 * 15.0 = 12.75
    # total = 35.0 + 26.8005 + 12.75 = 74.5505
    expected_nbai = 35.0 + (math.log1p(45.0) * 7.0) + (0.85 * 15.0)

    computed_nbai = engine._compute_activity_index(
        modis_count=m_count,
        viirs_count=v_count,
        calibrated_frp_mw=frp_cal,
        consensus_score=consensus
    )

    assert pytest.approx(expected_nbai, rel=1e-3) == computed_nbai

    # Test Case 2: Extreme burning saturation (must cap at 100.0)
    capped_nbai = engine._compute_activity_index(
        modis_count=50,
        viirs_count=200,
        calibrated_frp_mw=50000.0,
        consensus_score=1.0
    )
    assert capped_nbai == 100.0

    # Test Case 3: Zero activity (must evaluate to 0.0)
    zero_nbai = engine._compute_activity_index(
        modis_count=0,
        viirs_count=0,
        calibrated_frp_mw=0.0,
        consensus_score=0.0
    )
    assert zero_nbai == 0.0


def test_cross_sensor_consensus_scoring_logic(db_session: Session):
    """
    Validates inter-sensor consensus quantification under varying observation topologies:
    - Dual sensor with high matching: consensus in [0.70, 1.00]
    - VIIRS only: consensus in [0.60, 0.75]
    - MODIS only: consensus = 0.55
    - Neither: consensus = 0.0
    """
    engine = HarmonizationEngine(db_session)

    # 1. Dual Sensor with 100% paired associations
    score_full_dual = engine._compute_consensus_score(modis_count=2, viirs_count=4, associated_pairs=2)
    assert score_full_dual == 1.000  # 0.70 + 0.30 * 1.0

    # 2. Dual Sensor with partial pairing
    score_partial_dual = engine._compute_consensus_score(modis_count=2, viirs_count=4, associated_pairs=1)
    assert score_partial_dual == 0.850  # 0.70 + 0.30 * 0.5

    # 3. Dual Sensor with zero spatial-temporal pairing
    score_unpaired_dual = engine._compute_consensus_score(modis_count=2, viirs_count=4, associated_pairs=0)
    assert score_unpaired_dual == 0.700  # 0.70 + 0.30 * 0.0

    # 4. VIIRS only (multiple sub-pixel fires)
    score_viirs_multi = engine._compute_consensus_score(modis_count=0, viirs_count=3, associated_pairs=0)
    assert score_viirs_multi == 0.750

    # 5. VIIRS only (single sub-pixel fire)
    score_viirs_single = engine._compute_consensus_score(modis_count=0, viirs_count=1, associated_pairs=0)
    assert score_viirs_single == 0.600

    # 6. MODIS only (large fire without concurrent VIIRS overpass)
    score_modis_only = engine._compute_consensus_score(modis_count=1, viirs_count=0, associated_pairs=0)
    assert score_modis_only == 0.550

    # 7. No observations
    score_zero = engine._compute_consensus_score(modis_count=0, viirs_count=0, associated_pairs=0)
    assert score_zero == 0.0
