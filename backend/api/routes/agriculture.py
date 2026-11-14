"""
Agricultural Fire Context Intelligence API Endpoints.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.database import get_db
from backend.models.entities import CropCalendar, AgriculturalContextAssessment
from backend.services.agriculture.crop_calendar_service import CropCalendarService
from backend.services.agriculture.classification_service import AgriculturalClassificationService
from backend.schemas.agriculture import (
    CropCalendarCreate,
    CropCalendarResponse,
    AgriculturalClassificationRequest,
    AgriculturalContextAssessmentResponse,
    AgriculturalContextSummary
)

router = APIRouter(prefix="/agriculture", tags=["Agricultural Context Intelligence"])


@router.get("/calendars", response_model=List[CropCalendarResponse])
def get_crop_calendars(
    state_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves authoritative crop calendars with sowing, harvest, and residue burn windows."""
    svc = CropCalendarService(db)
    return svc.get_all_calendars(state_name=state_name)


@router.post("/calendars", response_model=CropCalendarResponse)
def create_crop_calendar(
    payload: CropCalendarCreate,
    db: Session = Depends(get_db)
):
    """Registers an official agricultural crop calendar."""
    cal = CropCalendar(**payload.model_dump())
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return cal


@router.get("/assessments", response_model=List[AgriculturalContextAssessmentResponse])
def get_assessments(
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    context_classification: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves agricultural context classifications for satellite fire observations."""
    stmt = select(AgriculturalContextAssessment)
    filters = []
    if date_start:
        filters.append(AgriculturalContextAssessment.observation_date >= date_start)
    if date_end:
        filters.append(AgriculturalContextAssessment.observation_date <= date_end)
    if context_classification:
        filters.append(AgriculturalContextAssessment.context_classification == context_classification)
    if filters:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(AgriculturalContextAssessment.observation_date.desc())
    return list(db.scalars(stmt).all())


@router.post("/classify", response_model=List[AgriculturalContextAssessmentResponse])
def classify_fire_activity(
    payload: AgriculturalClassificationRequest,
    db: Session = Depends(get_db)
):
    """Executes evidence-based agricultural fire context classification across harmonized observations."""
    svc = AgriculturalClassificationService(db)
    assessments = svc.classify_harmonized_records(
        date_start=payload.date_start,
        date_end=payload.date_end,
        state_name=payload.state_name
    )
    return assessments


@router.get("/summary", response_model=AgriculturalContextSummary)
def get_agricultural_summary(
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Computes distribution metrics and breakdown of agricultural fire classifications."""
    svc = AgriculturalClassificationService(db)
    return svc.get_summary(date_start=date_start, date_end=date_end)
