"""
Performance & Scalability Benchmark Suite.
Measures execution latency, algorithmic throughput, and computational overhead
to ensure production readiness under heavy computational loads.
"""

import time
import pytest
from sqlalchemy.orm import Session

from backend.services.geospatial.service import GeospatialService
from backend.services.routing.road_network_service import RoadNetworkService
from backend.services.economics.financial_engine import FinancialEngineService
from backend.services.environmental.lca_engine import LifeCycleAssessmentService
from backend.core.security.auth import create_access_token, decode_token
from backend.schemas.advanced_economics import FinancialScenarioCreate
from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate


def test_benchmark_geospatial_distance_throughput():
    """
    Benchmarks 10,000 spherical distance calculations.
    Must execute in less than 200 milliseconds.
    """
    geo = GeospatialService()
    start = time.perf_counter()
    for i in range(10000):
        geo.haversine_distance(30.70 + (i * 0.0001), 76.20, 30.80, 76.30)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.20, f"Geospatial throughput too slow: {elapsed:.3f}s for 10k points"


def test_benchmark_two_opt_routing_convergence():
    """
    Benchmarks 2-Opt local search TSP solution for a 15-stop rural collection route.
    Must converge in less than 300 milliseconds.
    """
    svc = RoadNetworkService()
    depot = (30.7000, 76.2000)
    stops = [
        {"farm_id": i, "latitude": 30.70 + (i * 0.01), "longitude": 76.20 + ((i % 3) * 0.01), "biomass_tons": 5.0}
        for i in range(15)
    ]

    start = time.perf_counter()
    solution = svc.solve_multi_stop_route(depot, stops)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.30, f"2-Opt routing too slow: {elapsed:.3f}s"
    assert len([s for s in solution["sequenced_stops"] if s.get("action") == "FARM_COLLECTION"]) == 15


def test_benchmark_financial_dcf_evaluation_speed(db_session: Session):
    """
    Benchmarks 50 multi-year DCF, NPV, and IRR scenarios.
    Must complete in less than 500 milliseconds.
    """
    svc = FinancialEngineService(db_session)
    payload = FinancialScenarioCreate(
        scenario_name="Benchmark Scenario",
        biomass_processed_tons=1000.0,
        briquette_price_per_ton=6000.0,
        biochar_price_per_ton=15000.0
    )

    start = time.perf_counter()
    for _ in range(50):
        svc.evaluate_scenario(payload)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.50, f"Financial evaluation too slow: {elapsed:.3f}s for 50 scenarios"


def test_benchmark_lca_calculation_throughput(db_session: Session):
    """
    Benchmarks 100 Life Cycle Assessment cradle-to-grave GHG balances.
    Must complete in less than 300 milliseconds.
    """
    svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1000.0,
        transport_fuel_liters=2500.0,
        processing_fuel_liters=4000.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20
    )

    start = time.perf_counter()
    for _ in range(100):
        svc.conduct_lca(payload)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.30, f"LCA calculation too slow: {elapsed:.3f}s for 100 evaluations"


def test_benchmark_jwt_token_creation_and_verification():
    """
    Benchmarks 500 JWT signing and HMAC cryptographic verification cycles.
    Must complete in less than 250 milliseconds.
    """
    start = time.perf_counter()
    for i in range(500):
        tok = create_access_token(user_id=i, username=f"user_{i}", role="FARMER")
        decode_token(tok)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.25, f"JWT verification too slow: {elapsed:.3f}s for 500 cycles"
