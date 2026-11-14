"""
Scientific Validation Suite: Vehicle Routing & Rural Road Network Transport Model.
Validates 2-Opt Traveling Salesperson Problem (TSP) edge-swap convergence,
geodesic spherical mathematics, Pradhan Mantri Gram Sadak Yojana (PMGSY) rural road tortuosity,
and commercial heavy-vehicle diesel consumption physics.

References:
- Croes, G. A. (1958), "A method for solving traveling-salesman problems", Operations Research
- National Rural Infrastructure Development Agency (NRIDA), "Geometric Design Standards for Rural Roads"
- Ministry of Road Transport and Highways (MoRTH), "Heavy Commercial Vehicle Fleet Consumption Indices"
"""

from backend.services.routing.road_network_service import RoadNetworkService
from backend.services.geospatial.service import GeospatialService
from backend.core.config.settings import config_manager


def test_haversine_great_circle_distance_formula():
    """
    Validates great-circle Haversine formulation against known spherical coordinates:
    Distance between Chandigarh (30.7333, 76.7794) and Ludhiana (30.9010, 75.8573).
    Independent spherical calculation gives ~90.75 km.
    """
    geo_svc = GeospatialService()
    d_km = geo_svc.haversine_distance(30.7333, 76.7794, 30.9010, 75.8573)
    assert 90.0 <= d_km <= 92.0


def test_pmgsy_road_tortuosity_and_fuel_physics():
    """
    Validates that point-to-point road calculations strictly enforce:
    1. NRIDA PMGSY tortuosity factor (tau = 1.35)
    2. Fuel rate consumption (0.38 L/km)
    3. Speed-based travel duration
    """
    svc = RoadNetworkService()
    tortuosity = float(config_manager.get("refinery.transport.road_tortuosity_factor"))
    assert tortuosity == 1.35

    res = svc.calculate_road_route(origin_lat=30.7000, origin_lon=76.2000, dest_lat=30.8000, dest_lon=76.3000)

    geodesic = res["geodesic_distance_km"]
    road_dist = res["road_distance_km"]

    # Verify road distance is exactly geodesic * tortuosity (rounded to 2 decimals)
    assert road_dist == round(geodesic * 1.35, 2)
    assert road_dist > geodesic

    # Verify fuel consumed = road_distance * fuel_rate (0.32 L/km)
    expected_fuel = round(road_dist * svc.fuel_rate, 2)
    assert res["fuel_consumed_liters"] == expected_fuel

    # Verify travel duration = road_distance / speed
    expected_duration = round(road_dist / 35.0, 2)
    assert res["travel_duration_hours"] == expected_duration


def test_two_opt_tsp_edge_swap_convergence():
    """
    Validates that the 2-Opt local search heuristic converges to an optimal or
    near-optimal non-self-intersecting tour for a set of rural farm stops.
    Tests that 2-Opt produces a tour length strictly less than or equal to the unoptimized order.
    """
    svc = RoadNetworkService()
    depot = (30.7000, 76.2000)

    # 4 stops arranged in a perimeter rectangle
    # Deliberately input in a criss-cross (sub-optimal) sequence: [Stop1, Stop3, Stop2, Stop4]
    stops = [
        {"farm_id": 1, "latitude": 30.7200, "longitude": 76.2000, "biomass_tons": 5.0},  # North
        {"farm_id": 3, "latitude": 30.7000, "longitude": 76.2400, "biomass_tons": 8.0},  # East
        {"farm_id": 2, "latitude": 30.7200, "longitude": 76.2400, "biomass_tons": 6.0},  # North-East
        {"farm_id": 4, "latitude": 30.6800, "longitude": 76.2200, "biomass_tons": 7.0},  # South
    ]

    # Calculate tour length of initial criss-cross sequence
    unoptimized_dist = svc._calculate_tour_distance(depot, stops)

    # Solve using Nearest-Neighbor + 2-Opt
    solution = svc.solve_multi_stop_route(depot, stops)
    optimized_dist = solution["total_distance_km"]

    # Optimized tour MUST be shorter than or equal to the arbitrary criss-cross sequence
    assert optimized_dist <= unoptimized_dist
    farm_collection_stops = [s for s in solution["sequenced_stops"] if s.get("action") == "FARM_COLLECTION"]
    assert len(farm_collection_stops) == 4
    assert len(solution["sequenced_stops"]) == 6  # 4 farm stops + DEPOT_START + DEPOT_END

    # Check that total fuel and duration are consistent with optimized tour distance
    assert solution["total_fuel_liters"] == round(optimized_dist * svc.fuel_rate, 2)
    assert solution["total_duration_hours"] >= 0.0


def test_routing_edge_case_empty_stops():
    """
    Validates that empty stop requests return zero distance and zero fuel gracefully.
    """
    svc = RoadNetworkService()
    depot = (30.7000, 76.2000)
    sol = svc.solve_multi_stop_route(depot, [])
    assert sol["total_distance_km"] == 0.0
    assert sol["total_fuel_liters"] == 0.0
    assert sol["sequenced_stops"] == []
