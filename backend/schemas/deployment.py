"""
Pydantic Schemas for Mobile Bio-Refinery Fleet, Deployment Planning, and Route Optimization.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MobileRefineryCreate(BaseModel):
    unit_code: str = Field(..., description="Unique unit identifier, e.g. MBR-PB-01")
    name: str
    equipment_type: str = "TRAILER_MOUNTED_DENSIFIER"
    technology: str = "BRIQUETTING"  # BRIQUETTING, SLOW_PYROLYSIS
    hourly_capacity_tons: float = Field(2.5, gt=0.0)
    daily_operating_hours: float = Field(10.0, gt=0.0, le=24.0)
    fuel_consumption_liters_per_ton: float = Field(4.5, gt=0.0)
    operating_cost_per_hour_inr: float = Field(750.0, gt=0.0)
    home_depot_name: str = "Ludhiana Central Depot"
    home_latitude: float = 30.9010
    home_longitude: float = 75.8573
    max_travel_radius_km: float = 60.0


class MobileRefineryResponse(MobileRefineryCreate):
    id: int
    daily_capacity_tons: float
    current_status: str
    is_active: bool
    created_at: datetime


class DeploymentPlanCreate(BaseModel):
    name: str
    region: str = "Punjab"
    date_start: date
    date_end: date
    unit_ids: Optional[List[int]] = None
    max_travel_radius_km: Optional[float] = None


class DeploymentAssignmentResponse(BaseModel):
    id: int
    deployment_plan_id: int
    mobile_unit_id: int
    unit_code: str
    farm_id: int
    farm_name: str
    assigned_biomass_tons: float
    scheduled_date: date
    collection_status: str


class RouteStopSchema(BaseModel):
    sequence: int
    stop_name: str
    latitude: float
    longitude: float
    action: str  # DEPOT_START, FARM_COLLECTION, DEPOT_END
    payload_tons: float
    distance_from_prev_km: float


class RoutePlanResponse(BaseModel):
    id: int
    deployment_plan_id: int
    mobile_unit_id: int
    unit_code: str
    route_date: date
    total_distance_km: float
    road_tortuosity_ratio: float
    estimated_duration_hours: float
    fuel_consumed_liters: float
    total_payload_tons: float
    stops: List[RouteStopSchema] = []
    created_at: datetime


class DeploymentPlanResponse(BaseModel):
    id: int
    plan_code: str
    name: str
    region: str
    date_start: date
    date_end: date
    status: str
    total_biomass_assigned_tons: float
    total_units_deployed: int
    total_route_distance_km: float
    estimated_transport_cost_inr: float
    unserved_farms_count: int
    capacity_utilization_pct: float
    assignments: List[DeploymentAssignmentResponse] = []
    routes: List[RoutePlanResponse] = []
    created_at: datetime
