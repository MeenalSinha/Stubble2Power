"""
Multi-Unit Deployment Planner & Fleet Vehicle Routing Service.
Solves capacity-constrained rural biomass collection, vehicle routing with road tortuosity,
and multi-objective deployment scenarios.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from backend.models.entities import (
    Farm,
    FarmCrop,
    Farmer,
    ConsentRecord,
    BiomassEstimate,
    DeploymentPlan,
    DeploymentAssignment,
    RoutePlan
)
from backend.schemas.deployment import DeploymentPlanCreate
from backend.services.routing.road_network_service import RoadNetworkService
from backend.services.deployment.refinery_service import MobileRefineryService
from backend.services.biomass.inventory_service import BiomassInventoryService
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import NotFoundError, ValidationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.deployment.planner")


class DeploymentPlannerService:
    def __init__(self, db: Session):
        self.db = db
        self.road_svc = RoadNetworkService()
        self.refinery_svc = MobileRefineryService(db)
        self.inventory_svc = BiomassInventoryService(db)
        self.diesel_price = float(config_manager.get("economics.diesel_price_inr_per_liter"))

    def plan_deployment(
        self,
        payload: DeploymentPlanCreate,
        strategy: str = "BALANCED"
    ) -> DeploymentPlan:
        """
        Generates an optimized multi-unit deployment plan respecting daily throughput,
        maximum radius constraints, and road tortuosity routing.
        """
        if payload.date_end < payload.date_start:
            raise ValidationError("End date cannot precede start date.", field="date_end")

        operating_days = max(1, (payload.date_end - payload.date_start).days + 1)

        # 1. Select available mobile bio-refineries
        if payload.unit_ids:
            units = [self.refinery_svc.get_unit(uid) for uid in payload.unit_ids]
        else:
            units = self.refinery_svc.list_units(status="AVAILABLE")
            if not units:
                # Fallback to all active units
                units = self.refinery_svc.list_units()

        if not units:
            raise ValidationError("No active mobile bio-refineries registered in fleet.")

        # 2. Query candidate biomass estimates in region and date window
        # Downstream DPDP Consent Enforcement: Fetch set of farmers who actively withdrew logistics/dispatch consent
        withdrawn_farmer_ids = set(
            self.db.scalars(
                select(ConsentRecord.farmer_id)
                .where(
                    and_(
                        ConsentRecord.consent_purpose.in_(["LOGISTICS_DISPATCH", "BIOMASS_AGGREGATION", "DATA_PROCESSING"]),
                        ConsentRecord.is_granted == False
                    )
                )
            ).all()
        )

        estimates_stmt = (
            select(BiomassEstimate, FarmCrop, Farm, Farmer)
            .join(FarmCrop, BiomassEstimate.farm_crop_id == FarmCrop.id)
            .join(Farm, FarmCrop.farm_id == Farm.id)
            .join(Farmer, Farm.farmer_id == Farmer.id)
            .where(
                and_(
                    BiomassEstimate.net_usable_biomass_tons > 0,
                    BiomassEstimate.availability_start_date <= payload.date_end,
                    BiomassEstimate.availability_end_date >= payload.date_start,
                    Farmer.consent_given == True
                )
            )
        )
        if payload.region and payload.region.upper() != "ALL":
            # Match state or district
            estimates_stmt = estimates_stmt.where(
                (Farm.state.ilike(f"%{payload.region}%")) | (Farm.district.ilike(f"%{payload.region}%"))
            )

        candidates_raw = self.db.execute(estimates_stmt).all()

        candidate_farms: List[Dict[str, Any]] = []
        seen_farms = set()
        for est, crop, farm, farmer in candidates_raw:
            # Downstream consent check: Exclude any farm with withdrawn processing consent
            if farm.farmer_id in withdrawn_farmer_ids:
                logger.info(
                    f"Consent enforcement: Farm ID {farm.id} ({farm.farm_name}) excluded "
                    f"because landholder {farm.farmer_id} withdrew processing/dispatch consent."
                )
                continue

            # Check already allocated tonnage in active plans
            allocated_tons = self.db.scalar(
                select(func.coalesce(func.sum(DeploymentAssignment.assigned_biomass_tons), 0.0))
                .where(
                    and_(
                        DeploymentAssignment.farm_id == farm.id,
                        DeploymentAssignment.collection_status.in_(["SCHEDULED", "PICKED_UP", "PROCESSED"])
                    )
                )
            ) or 0.0

            avail_tons = max(0.0, est.net_usable_biomass_tons - allocated_tons)
            if avail_tons > 0.1 and farm.id not in seen_farms:
                seen_farms.add(farm.id)
                candidate_farms.append({
                    "farm_id": farm.id,
                    "farm_name": farm.farm_name,
                    "latitude": farm.latitude,
                    "longitude": farm.longitude,
                    "biomass_tons": avail_tons,
                    "estimate_id": est.id,
                    "district": farm.district,
                    "crop_type": crop.crop_type
                })

        if not candidate_farms:
            raise ValidationError(
                f"No unallocated biomass available in {payload.region} for the requested window "
                f"({payload.date_start} to {payload.date_end})."
            )

        # 3. Initialize Unit Capacities
        unit_capacity: Dict[int, float] = {}
        unit_remaining: Dict[int, float] = {}
        for u in units:
            cap = round(u.daily_capacity_tons * operating_days, 2)
            unit_capacity[u.id] = cap
            unit_remaining[u.id] = cap

        # 4. Strategy sorting
        if strategy == "MAX_BIOMASS":
            candidate_farms.sort(key=lambda x: x["biomass_tons"], reverse=True)
        elif strategy == "MIN_COST":
            # Sort by distance to nearest depot
            def min_depot_dist(f):
                return min(
                    self.road_svc.geo_svc.haversine_distance(f["latitude"], f["longitude"], u.home_latitude, u.home_longitude)
                    for u in units
                )
            candidate_farms.sort(key=min_depot_dist)
        else:  # BALANCED
            candidate_farms.sort(key=lambda x: x["biomass_tons"], reverse=True)

        # 5. Assign candidate farms to units
        assignments_per_unit: Dict[int, List[Dict[str, Any]]] = {u.id: [] for u in units}
        unserved_farms: List[Dict[str, Any]] = []

        for farm in candidate_farms:
            f_lat, f_lon = farm["latitude"], farm["longitude"]
            f_tons = farm["biomass_tons"]

            # Find compatible units within travel radius
            compatible_units = []
            for u in units:
                max_rad = payload.max_travel_radius_km or u.max_travel_radius_km
                dist_to_depot = self.road_svc.geo_svc.haversine_distance(f_lat, f_lon, u.home_latitude, u.home_longitude)
                if dist_to_depot <= max_rad and unit_remaining[u.id] >= 1.0:
                    compatible_units.append((dist_to_depot, u))

            if not compatible_units:
                unserved_farms.append({
                    "farm_id": farm["farm_id"],
                    "farm_name": farm["farm_name"],
                    "biomass_tons": f_tons,
                    "reason": "OUT_OF_RANGE_OR_FLEET_AT_CAPACITY"
                })
                continue

            # Pick closest compatible unit with capacity
            compatible_units.sort(key=lambda x: x[0])
            _, chosen_unit = compatible_units[0]

            allocatable = min(f_tons, unit_remaining[chosen_unit.id])
            unit_remaining[chosen_unit.id] -= allocatable

            assignments_per_unit[chosen_unit.id].append({
                "farm_id": farm["farm_id"],
                "farm_name": farm["farm_name"],
                "latitude": f_lat,
                "longitude": f_lon,
                "assigned_biomass_tons": round(allocatable, 2),
                "estimate_id": farm["estimate_id"]
            })

            if allocatable < f_tons:
                unserved_farms.append({
                    "farm_id": farm["farm_id"],
                    "farm_name": farm["farm_name"],
                    "biomass_tons": round(f_tons - allocatable, 2),
                    "reason": "PARTIALLY_SERVED_CAPACITY_LIMIT"
                })

        # 6. Build DeploymentPlan Record
        plan_code = f"DEP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        deployment_plan = DeploymentPlan(
            plan_code=plan_code,
            name=payload.name,
            region=payload.region,
            date_start=payload.date_start,
            date_end=payload.date_end,
            status="OPTIMIZED",
            unserved_farms_count=len(unserved_farms),
            parameters_json={
                "strategy": strategy,
                "operating_days": operating_days,
                "unserved_details": unserved_farms,
                "tortuosity_ratio": self.road_svc.tortuosity
            }
        )
        self.db.add(deployment_plan)
        self.db.flush()

        total_assigned_biomass = 0.0
        total_route_distance = 0.0
        total_transport_cost = 0.0
        units_deployed_count = 0

        # 7. Route Sequencing and Assignment Creation
        curr_sched_date = payload.date_start
        for unit in units:
            unit_assigned_farms = assignments_per_unit[unit.id]
            if not unit_assigned_farms:
                continue

            units_deployed_count += 1
            depot_coords = (unit.home_latitude, unit.home_longitude)

            # Solve vehicle route with road tortuosity
            route_stops_input = [
                {
                    "farm_id": f["farm_id"],
                    "farm_name": f["farm_name"],
                    "latitude": f["latitude"],
                    "longitude": f["longitude"],
                    "biomass_tons": f["assigned_biomass_tons"]
                }
                for f in unit_assigned_farms
            ]
            route_result = self.road_svc.solve_multi_stop_route(depot_coords, route_stops_input)

            route_distance = route_result["total_distance_km"]
            fuel_liters = route_result["total_fuel_liters"]
            route_cost = round(fuel_liters * self.diesel_price, 2)

            total_route_distance += route_distance
            total_transport_cost += route_cost

            unit_assigned_tons = sum(f["assigned_biomass_tons"] for f in unit_assigned_farms)
            total_assigned_biomass += unit_assigned_tons

            # Create RoutePlan record
            route_plan_rec = RoutePlan(
                deployment_plan_id=deployment_plan.id,
                mobile_unit_id=unit.id,
                route_date=curr_sched_date,
                total_distance_km=route_distance,
                road_tortuosity_ratio=self.road_svc.tortuosity,
                estimated_duration_hours=route_result["total_duration_hours"],
                fuel_consumed_liters=fuel_liters,
                total_payload_tons=round(unit_assigned_tons, 2),
                stops_json=route_result["sequenced_stops"]
            )
            self.db.add(route_plan_rec)

            # Create DeploymentAssignment records & inventory allocations
            for f in unit_assigned_farms:
                assignment = DeploymentAssignment(
                    deployment_plan_id=deployment_plan.id,
                    mobile_unit_id=unit.id,
                    farm_id=f["farm_id"],
                    assigned_biomass_tons=f["assigned_biomass_tons"],
                    scheduled_date=curr_sched_date,
                    collection_status="SCHEDULED"
                )
                self.db.add(assignment)

                # Record inventory transition to ALLOCATED
                self.inventory_svc.record_transaction(
                    biomass_estimate_id=f["estimate_id"],
                    farm_id=f["farm_id"],
                    stage="ALLOCATED",
                    quantity_tons=f["assigned_biomass_tons"],
                    allocated_unit_id=unit.id,
                    notes=f"Allocated under deployment plan {plan_code} for unit {unit.unit_code}"
                )

        # Total fleet capacity across deployed units
        total_fleet_capacity = sum(unit_capacity[u.id] for u in units if assignments_per_unit[u.id])
        utilization = (total_assigned_biomass / total_fleet_capacity * 100.0) if total_fleet_capacity > 0 else 0.0

        deployment_plan.total_biomass_assigned_tons = round(total_assigned_biomass, 2)
        deployment_plan.total_units_deployed = units_deployed_count
        deployment_plan.total_route_distance_km = round(total_route_distance, 2)
        deployment_plan.estimated_transport_cost_inr = round(total_transport_cost, 2)
        deployment_plan.capacity_utilization_pct = round(utilization, 1)

        self.db.commit()
        self.db.refresh(deployment_plan)
        logger.info(
            f"Deployment plan {plan_code} generated: {units_deployed_count} units, "
            f"{total_assigned_biomass}t assigned ({utilization:.1f}% utilization), {len(unserved_farms)} unserved."
        )
        return deployment_plan

    def get_deployment(self, plan_id: int) -> DeploymentPlan:
        plan = self.db.scalars(select(DeploymentPlan).where(DeploymentPlan.id == plan_id)).first()
        if not plan:
            raise NotFoundError(message=f"Deployment plan {plan_id} not found.", entity="DeploymentPlan")
        return plan

    def list_deployments(self, region: Optional[str] = None) -> List[DeploymentPlan]:
        stmt = select(DeploymentPlan)
        if region and isinstance(region, str) and region.upper() != "ALL":
            stmt = stmt.where(DeploymentPlan.region.ilike(f"%{region}%"))
        stmt = stmt.order_by(DeploymentPlan.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def cancel_deployment(self, plan_id: int) -> DeploymentPlan:
        plan = self.get_deployment(plan_id)
        plan.status = "CANCELLED"
        for a in plan.assignments:
            a.collection_status = "CANCELLED"
        self.db.commit()
        self.db.refresh(plan)
        logger.info(f"Deployment plan {plan.plan_code} cancelled.")
        return plan

    # Alias for API compatibility across test suites
    generate_deployment_plan = plan_deployment

