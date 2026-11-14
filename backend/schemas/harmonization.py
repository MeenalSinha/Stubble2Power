"""
Pydantic schemas for Scientific MODIS-VIIRS Harmonization.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HarmonizationRunCreate(BaseModel):
    name: str = Field(..., description="Descriptive label for this harmonization run")
    date_start: date
    date_end: date
    bbox: Optional[List[float]] = None
    country_code: Optional[str] = "IND"
    spatial_grid_resolution_deg: float = 0.05
    cross_sensor_distance_km: float = 1.5
    cross_sensor_time_window_hours: float = 3.0
    viirs_frp_calibration_slope: float = 1.04


class HarmonizedObservationSchema(BaseModel):
    grid_id: str
    observation_date: date
    centroid_lat: float
    centroid_lon: float
    modis_count: int
    viirs_count: int
    total_detections: int
    associated_pairs_count: int
    modis_mean_frp: Optional[float] = None
    viirs_mean_frp: Optional[float] = None
    harmonized_frp_mw: float
    harmonized_activity_index: float = Field(..., ge=0.0, le=100.0)
    consensus_score: float = Field(..., ge=0.0, le=1.0)
    uncertainty_level: str  # LOW, MODERATE, HIGH
    data_coverage_flag: str  # DUAL_SENSOR, VIIRS_ONLY, MODIS_ONLY, ZERO_DETECTED, MISSING_OVERPASS


class HarmonizationRunResponse(BaseModel):
    id: int
    run_uuid: str
    name: str
    date_start: date
    date_end: date
    grid_resolution_deg: float
    total_input_observations: int
    harmonized_cells_count: int
    associated_pairs_count: int
    sensor_breakdown: Dict[str, int] = Field(default_factory=dict)
    mean_consensus_score: float
    algorithm_version: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
