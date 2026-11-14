"""
Pydantic Schemas for Fire Activity Anomaly Detection and Diagnostic Explainability.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AnomalyDetectRequest(BaseModel):
    region_id: str = Field("Punjab", description="Region to analyze")
    date_start: date
    date_end: date
    zscore_threshold: Optional[float] = Field(None, ge=1.0, le=5.0)
    mad_threshold: Optional[float] = Field(None, ge=1.5, le=6.0)
    min_frp_mw: Optional[float] = Field(None, ge=0.5, le=100.0)


class AnomalyExplanation(BaseModel):
    summary: str
    metric_observed: float
    baseline_expected: float
    z_score: float
    mad_score: float
    statistical_evidence: str
    spatial_context: str
    data_sufficiency_reason: str


class AnomalyResponse(BaseModel):
    id: int
    observation_date: date
    grid_id: str
    region_id: str
    observed_activity: float
    baseline_metric: str
    baseline_value: float
    z_score: float
    mad_score: float
    ewma_score: float
    anomaly_type: str  # SPIKE, PROLONGED_ELEVATION, UNSEASONAL_TIMING, SPATIAL_CLUSTER, EARLY_ONSET, LATE_SURGE
    severity_level: str  # LOW, MODERATE, HIGH, CRITICAL
    data_sufficiency_flag: str  # SUFFICIENT, UNCERTAIN_LIMITED_BASELINE
    explanation_json: Dict[str, Any]
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    created_at: datetime


class AnomalySummaryResponse(BaseModel):
    total_anomalies: int
    severity_counts: Dict[str, int]
    type_counts: Dict[str, int]
    anomalies: List[AnomalyResponse]
