"""
Pydantic schemas for NASA FIRMS satellite observations, ingestion jobs, and quality control.
"""

from datetime import datetime, date
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class IngestionJobCreate(BaseModel):
    satellite: str = Field(..., description="Satellite platform: MODIS_NRT, MODIS_SP, VIIRS_NOAA20_NRT, VIIRS_SNPP_NRT, VIIRS_NOAA21_NRT")
    country_code: Optional[str] = Field(None, description="ISO 3166-1 alpha-3 country code e.g. IND")
    bbox: Optional[List[float]] = Field(None, description="[min_lon, min_lat, max_lon, max_lat]")
    date_start: date = Field(..., description="Start date of observation window")
    date_end: date = Field(..., description="End date of observation window")
    day_range: int = Field(default=1, ge=1, le=10, description="FIRMS API day range limit")


class IngestionJobResponse(BaseModel):
    id: int
    job_uuid: str
    satellite: str
    instrument: str
    source_endpoint: str
    date_start: date
    date_end: date
    status: str  # PENDING, RUNNING, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED, CANCELLED
    records_retrieved: int = 0
    records_valid: int = 0
    records_quarantined: int = 0
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NormalizedObservationSchema(BaseModel):
    id: Optional[int] = None
    source_record_hash: str
    satellite: str
    instrument: str  # MODIS, VIIRS
    product_version: str
    acquisition_date: date
    acquisition_time_utc: str
    timestamp_utc: datetime
    latitude: float
    longitude: float
    brightness: Optional[float] = None  # Kelvin
    bright_t31: Optional[float] = None  # Channel 31 Kelvin
    frp: Optional[float] = None  # Fire Radiative Power in MW
    confidence_raw: str  # e.g. "85" for MODIS or "nominal" / "high" for VIIRS
    confidence_normalized: float = Field(..., ge=0.0, le=1.0)  # Standardized 0.0 - 1.0
    daynight: str  # 'D' or 'N'
    scan: Optional[float] = None
    track: Optional[float] = None
    spatial_grid_id: Optional[str] = None
    is_valid: bool = True
    quarantine_reason: Optional[str] = None

    class Config:
        from_attributes = True


class QualityControlSummary(BaseModel):
    total_raw_records: int
    valid_records: int
    invalid_quarantined_records: int
    duplicate_records_skipped: int
    sensor_counts: Dict[str, int]
    date_range_covered: Dict[str, str]
    spatial_bbox_covered: Dict[str, float]
    processing_version: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
