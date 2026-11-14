"""
Unit Tests for Phase 11: Mobile Bio-Refinery Fleet & Route Optimization.
Tests mobile unit registration, NRIDA rural road network tortuosity modeling,
multi-stop vehicle routing, and capacity-constrained deployment planning.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.entities import Base, Farmer, Farm, FarmCrop, BiomassEstimate
from backend.services.deployment.refinery_service import MobileRefineryService
from backend.services.routing.road_network_service import RoadNetworkService
from backend.services.deployment.planner_service import DeploymentPlannerService
from backend.schemas.deployment import MobileRefineryCreate, DeploymentPlanCreate
from backend.core.exceptions.base import ValidationError


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed baseline farmer and farm
    farmer = Farmer(
        name="Jaswant Singh",
        district="Ludhiana",
        village="Jagraon",
        latitude=30.7800,
        longitude=75.4800,
        acres=50.0,
        stubble_tons=100.0,
        harvest_date=date(2024, 10, 25),
        consent_given=True,
    )
    session.add(farmer)
    session.flush()

    farm1 = Farm(
        farmer_id=farmer.id,
        farm_name="Jagraon Cluster Farm A",
        total_acres=20.0,
        latitude=30.7900,
        longitude=75.4900,
        district="Ludhiana",
        village="Jagraon",
        state="Punjab",
    )
    farm2 = Farm(
        farmer_id=farmer.id,
        farm_name="Jagraon Cluster Farm B",
        total_acres=30.0,
        latitude=30.8100,
        longitude=75.5100,
        district="Ludhiana",
        village="Jagraon",
        state="Punjab",
    )
    session.add_all([farm1, farm2])
    session.flush()

    crop1 = FarmCrop(farm_id=farm1.id, crop_type="PADDY", cultivated_acres=20.0, crop_season="Kharif", crop_year=2024)
    crop2 = FarmCrop(farm_id=farm2.id, crop_type="PADDY", cultivated_acres=30.0, crop_season="Kharif", crop_year=2024)
    session.add_all([crop1, crop2])
    session.flush()

    # Seed biomass estimates (30t and 45t usable)
    est1 = BiomassEstimate(
        farm_crop_id=crop1.id,
        gross_residue_tons=45.0,
        retained_residue_tons=11.25,
        collectable_residue_tons=33.75,
        net_usable_biomass_tons=30.0,
        dry_matter_tons=25.8,
        availability_start_date=date(2024, 10, 20),
        availability_end_date=date(2024, 11, 15),
    )
    est2 = BiomassEstimate(
        farm_crop_id=crop2.id,
        gross_residue_tons=65.0,
        retained_residue_tons=16.25,
        collectable_residue_tons=48.75,
        net_usable_biomass_tons=45.0,
        dry_matter_tons=38.7,
        availability_start_date=date(2024, 10, 20),
        availability_end_date=date(2024, 11, 15),
    )
    session.add_all([est1, est2])
    session.commit()

    yield session
    session.close()


def test_mobile_unit_registration_and_validation(db_session):
    ref_svc = MobileRefineryService(db_session)
    payload = MobileRefineryCreate(
        unit_code="MBR-LDH-01",
        name="Ludhiana Pioneer Densifier",
        technology="BRIQUETTING",
        hourly_capacity_tons=2.5,
        daily_operating_hours=10.0,
        fuel_consumption_liters_per_ton=4.5,
        home_depot_name="Ludhiana Ag Hub",
        home_latitude=30.9010,
        home_longitude=75.8573,
        max_travel_radius_km=50.0,
    )
    unit = ref_svc.register_unit(payload)
    assert unit.id is not None
    assert unit.unit_code == "MBR-LDH-01"
    assert unit.daily_capacity_tons == 25.0
    assert unit.current_status == "AVAILABLE"

    # Duplicate rejection
    with pytest.raises(ValidationError):
        ref_svc.register_unit(payload)


def test_road_network_tortuosity_modeling():
    road_svc = RoadNetworkService()
    # Ludhiana depot to Raikot
    origin = (30.9010, 75.8573)
    dest = (30.6512, 75.5984)

    route = road_svc.calculate_road_route(origin[0], origin[1], dest[0], dest[1])
    geodesic = route["geodesic_distance_km"]
    road_dist = route["road_distance_km"]

    # Verify NRIDA calibrated tortuosity factor application
    assert route["tortuosity_factor"] == pytest.approx(1.35, 0.05)
    assert road_dist == pytest.approx(geodesic * route["tortuosity_factor"], 0.1)
    assert route["travel_duration_hours"] > 0.0
    assert route["fuel_consumed_liters"] == pytest.approx(road_dist * road_svc.fuel_rate, 0.1)


def test_multi_stop_route_sequencing():
    road_svc = RoadNetworkService()
    depot = (30.9010, 75.8573)
    stops = [
        {"farm_name": "Farm Alpha", "latitude": 30.8200, "longitude": 75.6000, "biomass_tons": 25.0},
        {"farm_name": "Farm Beta", "latitude": 30.7500, "longitude": 75.5500, "biomass_tons": 35.0},
    ]

    result = road_svc.solve_multi_stop_route(depot, stops)
    assert result["total_distance_km"] > 0.0
    assert result["total_fuel_liters"] > 0.0

    seq = result["sequenced_stops"]
    assert len(seq) == 4  # Depot start + 2 farms + Depot return
    assert seq[0]["action"] == "DEPOT_START"
    assert seq[1]["action"] == "FARM_COLLECTION"
    assert seq[2]["action"] == "FARM_COLLECTION"
    assert seq[3]["action"] == "DEPOT_END"
    assert result["is_simulated_approximation"] is True
    assert result["optimization_method"] == "Nearest-Neighbor + 2-Opt Local Search"
    assert "iterations_executed" in result


def test_deployment_planner_capacity_and_routing(db_session):
    ref_svc = MobileRefineryService(db_session)
    ref_svc.register_unit(
        MobileRefineryCreate(
            unit_code="MBR-LDH-02",
            name="Ludhiana Unit 2",
            hourly_capacity_tons=2.5,
            daily_operating_hours=10.0,  # 25t/day
            home_latitude=30.8000,
            home_longitude=75.5000,
            max_travel_radius_km=30.0,
        )
    )

    planner_svc = DeploymentPlannerService(db_session)
    plan_req = DeploymentPlanCreate(
        name="Jagraon Harvest Campaign",
        region="Ludhiana",
        date_start=date(2024, 10, 22),
        date_end=date(2024, 10, 26),  # 5 days = 125t fleet capacity
    )

    plan = planner_svc.plan_deployment(plan_req, strategy="BALANCED")
    assert plan.id is not None
    assert plan.plan_code.startswith("DEP-")
    assert plan.status == "OPTIMIZED"
    assert plan.total_units_deployed == 1
    assert plan.total_biomass_assigned_tons == pytest.approx(75.0, 0.1)  # 30 + 45
    assert plan.unserved_farms_count == 0
    assert len(plan.assignments) == 2
    assert len(plan.routes) == 1
    assert plan.total_route_distance_km > 0.0
    assert plan.estimated_transport_cost_inr > 0.0
