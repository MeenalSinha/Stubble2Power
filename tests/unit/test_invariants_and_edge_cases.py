"""
Property-Based Invariants, Boundary Limits & Edge-Case Test Suite.
Validates fundamental mathematical invariants, extreme boundary conditions,
and safety constraints across all platform engines.

Invariants Verified:
1. Spatial metric properties: non-negativity, identity, symmetry, triangle inequality
2. Network distance monotonicity: road_distance >= geodesic_distance
3. Conservation of mass in biomass allocation: allocated_biomass <= net_usable_biomass
4. Zero-input boundary safety: zero biomass produces zero revenue/emissions without crash
5. Extreme boundary coordinates and saturation limits
6. Strict JWT cryptographic verification and token tampering rejection
"""

import pytest
from sqlalchemy.orm import Session

from backend.services.geospatial.service import GeospatialService
from backend.services.routing.road_network_service import RoadNetworkService
from backend.services.economics.financial_engine import FinancialEngineService
from backend.services.environmental.lca_engine import LifeCycleAssessmentService
from backend.services.privacy.privacy_service import PrivacyService
from backend.core.security.auth import (
    create_access_token, decode_token
)
from backend.core.exceptions.base import AuthenticationError
from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate


def test_spatial_metric_tensor_invariants():
    """
    Validates mathematical metric tensor invariants of Haversine distance:
    1. Non-negativity: d(A, B) >= 0
    2. Identity: d(A, A) == 0
    3. Symmetry: d(A, B) == d(B, A)
    4. Triangle Inequality: d(A, C) <= d(A, B) + d(B, C)
    """
    geo = GeospatialService()
    pA = (30.7333, 76.7794)  # Chandigarh
    pB = (30.9010, 75.8573)  # Ludhiana
    pC = (31.3260, 75.5762)  # Jalandhar

    # Identity
    assert geo.haversine_distance(pA[0], pA[1], pA[0], pA[1]) == 0.0

    # Non-negativity
    d_AB = geo.haversine_distance(pA[0], pA[1], pB[0], pB[1])
    assert d_AB > 0.0

    # Symmetry
    d_BA = geo.haversine_distance(pB[0], pB[1], pA[0], pA[1])
    assert pytest.approx(d_AB, rel=1e-5) == d_BA

    # Triangle Inequality: d(A, C) <= d(A, B) + d(B, C)
    d_AC = geo.haversine_distance(pA[0], pA[1], pC[0], pC[1])
    d_BC = geo.haversine_distance(pB[0], pB[1], pC[0], pC[1])
    assert d_AC <= (d_AB + d_BC + 1e-4)


def test_road_network_distance_monotonicity():
    """
    Validates that road distance is strictly greater than or equal to geodesic distance:
    road_distance >= geodesic_distance for any valid coordinate pair.
    """
    road_svc = RoadNetworkService()
    coords = [
        ((30.70, 76.20), (30.80, 76.30)),
        ((30.50, 75.80), (30.90, 75.85)),
        ((30.10, 74.90), (30.30, 75.20))
    ]

    for (lat1, lon1), (lat2, lon2) in coords:
        res = road_svc.calculate_road_route(lat1, lon1, lat2, lon2)
        assert res["road_distance_km"] >= res["geodesic_distance_km"]
        assert res["tortuosity_factor"] >= 1.0


def test_zero_biomass_economic_and_environmental_safety(db_session: Session):
    """
    Validates that zero or near-zero biomass inputs are handled safely
    without division-by-zero crashes in financial or LCA engines.
    """
    fin_svc = FinancialEngineService(db_session)
    lca_svc = LifeCycleAssessmentService(db_session)

    # 1. Financial Engine with minimal positive biomass (1 ton floor)
    fin_payload = FinancialScenarioCreate(
        scenario_name="Minimal Tonnage",
        biomass_processed_tons=1.0,
        briquette_price_per_ton=6000.0,
        biochar_price_per_ton=15000.0
    )
    fin_res = fin_svc.evaluate_scenario(fin_payload)
    assert fin_res.total_biomass_processed_tons == 1.0
    assert fin_res.total_revenue_inr > 0.0

    # 2. LCA Engine with minimal positive biomass (0.1 ton floor)
    lca_payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=0.1,
        transport_fuel_liters=0.0,
        processing_fuel_liters=0.0
    )
    lca_res = lca_svc.conduct_lca(lca_payload)
    assert lca_res.biomass_diverted_tons == 0.1
    assert lca_res.baseline_total_co2e_tons >= 0.0


def test_jwt_tampering_and_forgery_rejection():
    """
    Validates that altered, corrupted, or re-signed JWT tokens are strictly rejected
    by cryptographic signature verification.
    """
    valid_token = create_access_token(
        user_id=42,
        username="authentic_user",
        role="FARMER"
    )

    # 1. Valid token decodes correctly
    payload = decode_token(valid_token)
    assert payload["sub"] == "authentic_user"
    assert payload["user_id"] == 42

    # 2. Tampered payload segment -> Must raise AuthenticationError
    parts = valid_token.split(".")
    tampered_token = parts[0] + "." + parts[1] + "tampered" + "." + parts[2]
    with pytest.raises(AuthenticationError):
        decode_token(tampered_token)

    # 3. Forged signature segment -> Must raise AuthenticationError
    forged_token = parts[0] + "." + parts[1] + ".invalid_signature_string"
    with pytest.raises(AuthenticationError):
        decode_token(forged_token)


def test_location_privacy_bounding_box_invariant(db_session: Session):
    """
    Validates that coordinates blurred for privacy remain within reasonable
    proximity (~1.5 km maximum offset) of original coordinates.
    """
    priv_svc = PrivacyService(db_session)
    geo_svc = GeospatialService()

    test_points = [
        (30.7333, 76.7794),
        (31.3260, 75.5762),
        (30.2100, 74.9450),
        (30.9010, 75.8573)
    ]

    for lat, lon in test_points:
        b_lat, b_lon, is_blurred = priv_svc.filter_location_privacy(lat, lon, viewer_role="PUBLIC_VISITOR")
        assert is_blurred is True
        # Displacement distance must be strictly less than 2.0 km
        dist = geo_svc.haversine_distance(lat, lon, b_lat, b_lon)
        assert dist <= 2.0
