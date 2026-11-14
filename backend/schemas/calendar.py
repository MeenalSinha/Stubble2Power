"""
Pydantic schemas for the Historical Burning Activity Calendar.
"""

from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DailyCalendarEntry(BaseModel):
    date: date
    day_of_week: str
    modis_detections: int
    viirs_detections: int
    total_detections: int
    associated_detections: int
    harmonized_activity_index: float  # 0.0 to 100.0
    total_frp_mw: float
    coverage_status: str  # COMPLETE, PARTIAL_MODIS, PARTIAL_VIIRS, NO_OVERPASS, ZERO_BURNING
    data_quality_flags: List[str] = []


class WeeklyCalendarSummary(BaseModel):
    week_number: int
    year: int
    start_date: date
    end_date: date
    total_detections: int
    modis_detections: int
    viirs_detections: int
    mean_daily_activity: float
    peak_date: Optional[date] = None
    peak_detections: int = 0


class MonthlyCalendarSummary(BaseModel):
    year: int
    month: int
    month_name: str
    total_detections: int
    modis_detections: int
    viirs_detections: int
    mean_daily_activity: float
    active_burning_days: int
    peak_date: Optional[date] = None
    peak_detections: int = 0


class AnnualCalendarSummary(BaseModel):
    year: int
    total_detections: int
    modis_detections: int
    viirs_detections: int
    burning_season_start: Optional[date] = None
    burning_season_peak: Optional[date] = None
    burning_season_end: Optional[date] = None
    seasonal_total_detections: int = 0
