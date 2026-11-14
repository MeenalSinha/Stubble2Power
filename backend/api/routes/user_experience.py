"""
User Experience API Routes.
Manages user preferences, real-time in-app notifications, and business report generation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import User
from backend.schemas.user_experience import (
    UserPreferenceUpdate, UserPreferenceResponse,
    NotificationResponse, SavedReportCreate, SavedReportResponse
)
from backend.services.user_experience.user_experience_service import UserExperienceService
from backend.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["User Experience & Personalization"])


@router.get("/preferences", response_model=UserPreferenceResponse)
def get_user_preferences(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves personalization preferences for the authenticated user."""
    ux_svc = UserExperienceService(db)
    return ux_svc.get_or_create_preferences(user.id)


@router.put("/preferences", response_model=UserPreferenceResponse)
def update_user_preferences(
    payload: UserPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates personalization preferences (language, theme, default AOI, layout)."""
    ux_svc = UserExperienceService(db)
    return ux_svc.update_preferences(user.id, payload)


@router.get("/notifications", response_model=List[NotificationResponse])
def get_user_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists recent system and operational notifications for the authenticated user."""
    ux_svc = UserExperienceService(db)
    return ux_svc.list_user_notifications(user.id, unread_only=unread_only, limit=limit)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks a notification as read."""
    ux_svc = UserExperienceService(db)
    return ux_svc.mark_notification_read(notification_id, user.id)


@router.post("/reports/generate", response_model=SavedReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: SavedReportCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates an auditable report snapshot from real database assets."""
    ux_svc = UserExperienceService(db)
    return ux_svc.generate_and_save_report(
        user_id=user.id,
        report_type=payload.report_type,
        title=payload.title,
        file_format=payload.file_format,
        organization_id=user.organization_id,
        parameters=payload.parameters_json
    )


@router.get("/reports", response_model=List[SavedReportResponse])
def list_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists saved reports for the authenticated user or organization."""
    ux_svc = UserExperienceService(db)
    user_role = (user.role_name or user.role or "").upper()
    if user_role == "SYSTEM_ADMINISTRATOR":
        return ux_svc.list_saved_reports(user_id=None)
    return ux_svc.list_saved_reports(user_id=user.id)
