"""
Pydantic Schemas for Agricultural Reference Data, Crop Calendars, and Fire Context Classification.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CropCalendarBase(BaseModel):
    crop_name: str = Field(..., description="Crop designation (e.g. Paddy / Rice (Kharif))")
    state_name: str = Field(..., description="State or province (e.g. Punjab)")
    district_name: str = Field("ALL", description="District or ALL")
    season_name: str = Field(..., description="Season: Kharif, Rabi, Zaid, Perennial")
    sowing_start_month_day: str = Field(..., description="MM-DD, e.g. 06-15")
    sowing_end_month_day: str = Field(..., description="MM-DD, e.g. 07-15")
    harvest_start_month_day: str = Field(..., description="MM-DD, e.g. 10-01")
    harvest_end_month_day: str = Field(..., description="MM-DD, e.g. 11-30")
    peak_burn_start_month_day: str = Field(..., description="MM-DD, e.g. 10-15")
    peak_burn_end_month_day: str = Field(..., description="MM-DD, e.g. 11-20")
    stubble_burning_susceptibility: str = Field("HIGH", description="HIGH, MEDIUM, LOW")
    official_source: str
    citation: str
    version: str = "1.0.0"
    is_active: bool = True


class CropCalendarCreate(CropCalendarBase):
    pass


class CropCalendarResponse(CropCalendarBase):
    id: int
    created_at: datetime


class LandUseRecordBase(BaseModel):
    zone_name: str
    state_name: str
    district_name: str
    land_use_class: str  # CROPLAND, FOREST, URBAN_INDUSTRIAL, WETLAND_WATER, BARREN_SCRUB
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    source: str = "ESA WorldCover 10m / NRSC Bhuvan"
    confidence: float = 0.90


class LandUseRecordCreate(LandUseRecordBase):
    pass


class LandUseRecordResponse(LandUseRecordBase):
    id: int
    created_at: datetime


class AgriculturalClassificationRequest(BaseModel):
    date_start: date
    date_end: date
    state_name: str = Field("Punjab", description="State name to filter")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class AgriculturalContextAssessmentResponse(BaseModel):
    id: int
    harmonized_observation_id: Optional[int] = None
    observation_date: date
    latitude: float
    longitude: float
    grid_id: str
    land_use_class: str
    land_use_confidence: float
    matched_crop: Optional[str] = None
    harvest_window_status: str  # IN_PEAK_HARVEST_WINDOW, IN_EXTENDED_HARVEST_WINDOW, OFF_SEASON, UNKNOWN
    context_classification: str  # LIKELY_AGRICULTURAL_CONTEXT, POSSIBLE_AGRICULTURAL_CONTEXT, OTHER_LAND_USE_CONTEXT, UNKNOWN_OR_INSUFFICIENT_EVIDENCE
    confidence_score: float
    distance_to_cropland_km: float
    stubble_risk_index: float
    evidence_json: Dict[str, Any]
    created_at: datetime


class AgriculturalContextSummary(BaseModel):
    total_assessed: int
    likely_agricultural_count: int
    possible_agricultural_count: int
    other_land_use_count: int
    unknown_count: int
    percent_likely_agricultural: float
    crop_breakdown: Dict[str, int]
    land_use_breakdown: Dict[str, int]
    assessments: List[AgriculturalContextAssessmentResponse]
