"""
Deployment Planning & Fleet Vehicle Routing API Routes.
Manages multi-unit deployment planning, capacity constrained routing, and route plan retrieval.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.deployment.planner_service import DeploymentPlannerService
from backend.models.entities import DeploymentPlan
from backend.schemas.deployment import (
    DeploymentPlanCreate,
    DeploymentPlanResponse,
    DeploymentAssignmentResponse,
    RoutePlanResponse
)
from backend.core.exceptions.base import ValidationError, NotFoundError

router = APIRouter(prefix="/deployments", tags=["Phase 11: Deployment Planning & Logistics"])


def format_deployment_plan(plan: DeploymentPlan) -> DeploymentPlanResponse:
    """Helper to convert DeploymentPlan ORM entity into Pydantic response."""
    assignments = []
    for a in plan.assignments:
        assignments.append(
            DeploymentAssignmentResponse(
                id=a.id,
                deployment_plan_id=a.deployment_plan_id,
                mobile_unit_id=a.mobile_unit_id,
                unit_code=a.mobile_unit.unit_code if a.mobile_unit else "UNKNOWN",
                farm_id=a.farm_id,
                farm_name=a.farm.farm_name if a.farm else f"Farm #{a.farm_id}",
                assigned_biomass_tons=a.assigned_biomass_tons,
                scheduled_date=a.scheduled_date,
                collection_status=a.collection_status
            )
        )
    routes = []
    for r in plan.routes:
        stops = r.stops_json if isinstance(r.stops_json, list) else []
        routes.append(
            RoutePlanResponse(
                id=r.id,
                deployment_plan_id=r.deployment_plan_id,
                mobile_unit_id=r.mobile_unit_id,
                unit_code=r.mobile_unit.unit_code if r.mobile_unit else "UNKNOWN",
                route_date=r.route_date,
                total_distance_km=r.total_distance_km,
                road_tortuosity_ratio=r.road_tortuosity_ratio,
                estimated_duration_hours=r.estimated_duration_hours,
                fuel_consumed_liters=r.fuel_consumed_liters,
                total_payload_tons=r.total_payload_tons,
                stops=stops,
                created_at=r.created_at
            )
        )
    return DeploymentPlanResponse(
        id=plan.id,
        plan_code=plan.plan_code,
        name=plan.name,
        region=plan.region,
        date_start=plan.date_start,
        date_end=plan.date_end,
        status=plan.status,
        total_biomass_assigned_tons=plan.total_biomass_assigned_tons,
        total_units_deployed=plan.total_units_deployed,
        total_route_distance_km=plan.total_route_distance_km,
        estimated_transport_cost_inr=plan.estimated_transport_cost_inr,
        unserved_farms_count=plan.unserved_farms_count,
        capacity_utilization_pct=plan.capacity_utilization_pct,
        assignments=assignments,
        routes=routes,
        created_at=plan.created_at
    )


@router.post("/plan", response_model=DeploymentPlanResponse, status_code=201)
def generate_deployment_plan(
    payload: DeploymentPlanCreate,
    strategy: str = Query("BALANCED", description="Optimization strategy: BALANCED, MAX_BIOMASS, MIN_COST"),
    db: Session = Depends(get_db)
):
    """Executes capacity-aware assignment and road network vehicle routing for target farms."""
    try:
        service = DeploymentPlannerService(db)
        plan = service.plan_deployment(payload, strategy=strategy)
        return format_deployment_plan(plan)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/", response_model=List[DeploymentPlanResponse])
def list_deployments(
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists existing deployment plans."""
    service = DeploymentPlannerService(db)
    plans = service.list_deployments(region=region)
    return [format_deployment_plan(p) for p in plans]


@router.get("/{plan_id}", response_model=DeploymentPlanResponse)
def get_deployment_plan(plan_id: int, db: Session = Depends(get_db)):
    """Retrieves deployment plan details including assignments and vehicle routes."""
    try:
        service = DeploymentPlannerService(db)
        plan = service.get_deployment(plan_id)
        return format_deployment_plan(plan)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/{plan_id}/cancel", response_model=DeploymentPlanResponse)
def cancel_deployment_plan(plan_id: int, db: Session = Depends(get_db)):
    """Cancels a scheduled or active deployment plan."""
    try:
        service = DeploymentPlannerService(db)
        plan = service.cancel_deployment(plan_id)
        return format_deployment_plan(plan)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/{plan_id}/routes", response_model=List[RoutePlanResponse])
def get_deployment_routes(plan_id: int, db: Session = Depends(get_db)):
    """Retrieves detailed vehicle route plans and stops for a deployment."""
    service = DeploymentPlannerService(db)
    plan = service.get_deployment(plan_id)
    routes = []
    for r in plan.routes:
        stops = r.stops_json if isinstance(r.stops_json, list) else []
        routes.append(
            RoutePlanResponse(
                id=r.id,
                deployment_plan_id=r.deployment_plan_id,
                mobile_unit_id=r.mobile_unit_id,
                unit_code=r.mobile_unit.unit_code if r.mobile_unit else "UNKNOWN",
                route_date=r.route_date,
                total_distance_km=r.total_distance_km,
                road_tortuosity_ratio=r.road_tortuosity_ratio,
                estimated_duration_hours=r.estimated_duration_hours,
                fuel_consumed_liters=r.fuel_consumed_liters,
                total_payload_tons=r.total_payload_tons,
                stops=stops,
                created_at=r.created_at
            )
        )
    return routes
