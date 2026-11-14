"""
Historical Burning Activity Calendar API Endpoints.
"""

from typing import List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.services.calendar.service import CalendarAggregationService
from backend.schemas.calendar import (
    DailyCalendarEntry,
    WeeklyCalendarSummary,
    MonthlyCalendarSummary,
    AnnualCalendarSummary
)

router = APIRouter(prefix="/calendar", tags=["Activity Calendar"])


@router.get("/daily", response_model=List[DailyCalendarEntry])
def get_daily_calendar(
    date_start: date = Query(...),
    date_end: date = Query(...),
    db: Session = Depends(get_db)
):
    """Retrieves continuous daily activity calendar entries."""
    svc = CalendarAggregationService(db)
    return svc.get_daily_calendar(date_start=date_start, date_end=date_end)


@router.get("/weekly", response_model=List[WeeklyCalendarSummary])
def get_weekly_calendar(
    year: int = Query(2025, ge=2000, le=2035),
    db: Session = Depends(get_db)
):
    """Retrieves weekly aggregated burning activity summaries."""
    svc = CalendarAggregationService(db)
    return svc.get_weekly_summaries(year=year)


@router.get("/monthly", response_model=List[MonthlyCalendarSummary])
def get_monthly_calendar(
    year: int = Query(2025, ge=2000, le=2035),
    db: Session = Depends(get_db)
):
    """Retrieves monthly burning patterns and seasonal distribution."""
    svc = CalendarAggregationService(db)
    return svc.get_monthly_summaries(year=year)


@router.get("/annual", response_model=AnnualCalendarSummary)
def get_annual_summary(
    year: int = Query(2025, ge=2000, le=2035),
    db: Session = Depends(get_db)
):
    """Retrieves annual trend and detected peak burning dates."""
    svc = CalendarAggregationService(db)
    return svc.get_annual_summary(year=year)
