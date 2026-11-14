"""
Pydantic Schemas for Seasonal Fire Intelligence and Historical Baselines.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BaselineComputeRequest(BaseModel):
    region_id: str = Field("Punjab", description="Administrative region or state identifier")
    analysis_period: str = Field("OCT_NOV_MULTIYEAR", description="Historical baseline period name")
    metric_type: str = Field(
        "harmonized_frp_mw", description="Metric to baseline: harmonized_frp_mw, activity_index, detections"
    )
    window_days: int = Field(15, ge=3, le=60, description="Centered rolling smoothing window")
    min_periods: int = Field(3, ge=1, le=30, description="Minimum periods for sufficient history")


class BaselineEntry(BaseModel):
    id: Optional[int] = None
    region_id: str
    grid_id: Optional[str] = None
    analysis_period: str
    metric_type: str
    day_of_year: Optional[int] = None
    mean_val: float
    median_val: float
    std_val: float
    mad_val: float
    p75_val: float
    p90_val: float
    min_val: float
    max_val: float
    sample_count: int
    data_coverage_ratio: float
    data_sufficiency_status: str


class SeasonalProfileCreate(BaseModel):
    region_id: str = Field("Punjab", description="Region identifier")
    year: int = Field(2026, ge=2000, le=2100)
    season_name: str = Field(
        "Kharif_PostHarvest", description="Name of season (Kharif_PostHarvest, Rabi_PostHarvest, Annual)"
    )
    date_start: date
    date_end: date


class SeasonalProfileResponse(BaseModel):
    id: int
    region_id: str
    year: int
    season_name: str
    onset_date: Optional[date] = None
    peak_date: Optional[date] = None
    decay_date: Optional[date] = None
    total_activity: float
    peak_activity: float
    duration_days: int
    profile_curve_json: Dict[str, Any] = {}
    created_at: datetime


class SeasonalProfileSummary(BaseModel):
    profiles: List[SeasonalProfileResponse]
    multiyear_average_peak_date: Optional[str] = None
    earliest_onset_recorded: Optional[str] = None
    latest_decay_recorded: Optional[str] = None
