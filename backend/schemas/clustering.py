"""
Pydantic schemas for Farmer Clustering and Mobile Unit Logistics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ClusterPoint(BaseModel):
    id: Optional[int] = None
    farmer_name: str
    village: str
    district: str
    latitude: float
    longitude: float
    stubble_tons: float
    cluster: int


class ClusterMetricItem(BaseModel):
    cluster_id: int
    total_stubble_tons: float
    farmer_count: int
    village_count: int
    avg_distance_km: float
    transport_cost_inr: float
    center_latitude: float
    center_longitude: float
    processing_time_hours: float


class ClusteringResult(BaseModel):
    scenario: str
    n_clusters: int
    total_farmers: int
    total_stubble_tons: float
    total_mobile_transport_cost_inr: float
    central_plant_cost_inr: float
    logistics_savings_inr: float
    logistics_reduction_pct: float
    cluster_metrics: List[ClusterMetricItem]
    assigned_points: List[ClusterPoint]
