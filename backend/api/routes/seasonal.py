"""
Seasonal Fire Intelligence and Baseline API Endpoints.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.seasonal.profile_service import SeasonalProfileService
from backend.services.seasonal.baseline_service import HistoricalBaselineService
from backend.schemas.seasonal import (
    SeasonalProfileCreate,
    SeasonalProfileResponse,
    BaselineComputeRequest,
    BaselineEntry
)

router = APIRouter(prefix="/seasonal", tags=["Seasonal Intelligence"])


@router.get("/profiles", response_model=List[SeasonalProfileResponse])
def get_seasonal_profiles(
    region_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves empirical seasonal profiles and burning activity curves."""
    svc = SeasonalProfileService(db)
    return svc.get_profiles(region_id=region_id)


@router.post("/profiles/generate", response_model=SeasonalProfileResponse)
def generate_seasonal_profile(
    payload: SeasonalProfileCreate,
    db: Session = Depends(get_db)
):
    """Extracts seasonal onset, peak, and decay dates from harmonized observations."""
    svc = SeasonalProfileService(db)
    profile = svc.generate_profile(
        region_id=payload.region_id,
        year=payload.year,
        season_name=payload.season_name,
        date_start=payload.date_start,
        date_end=payload.date_end
    )
    return profile


@router.get("/baselines", response_model=List[BaselineEntry])
def get_historical_baselines(
    region_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves calculated multi-year historical baselines and normals."""
    svc = HistoricalBaselineService(db)
    return svc.get_all_baselines(region_id=region_id, metric_type=metric_type)


@router.post("/baselines/compute", response_model=List[BaselineEntry])
def compute_baselines(
    payload: BaselineComputeRequest,
    db: Session = Depends(get_db)
):
    """Triggers baseline calculation for a region and period."""
    from backend.services.calendar.service import CalendarAggregationService
    cal_svc = CalendarAggregationService(db)
    
    # Query calendar daily entries for baseline source data
    # Use existing date range from observations
    today = date.today()
    start_date = today.replace(year=today.year - payload.min_periods, month=1, day=1)
    daily_entries = cal_svc.get_daily_calendar(date_start=start_date, date_end=today)
    
    records = [
        {
            "date": d.date,
            "harmonized_frp_mw": d.total_frp_mw,
            "activity_index": d.harmonized_activity_index,
            "detections": d.total_detections
        }
        for d in daily_entries
    ]
    
    svc = HistoricalBaselineService(db)
    baselines = svc.compute_baselines_from_data(
        daily_records=records,
        region_id=payload.region_id,
        analysis_period=payload.analysis_period,
        metric_type=payload.metric_type
    )
    return baselines
