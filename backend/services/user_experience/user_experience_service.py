"""
User Experience Service: Personalization, Notifications, and Exportable Reports.
Supports multi-language preferences, role-targeted notification feeds, and auditable data reporting.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from backend.models.entities import (
    UserPreference,
    Notification,
    SavedReport,
    Farmer,
    BiomassEstimate,
    DeploymentPlan,
    FinancialScenario,
    EnvironmentalAssessment,
)
from backend.schemas.user_experience import UserPreferenceUpdate
from backend.core.exceptions.base import NotFoundError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.ux.service")


class UserExperienceService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_preferences(self, user_id: int) -> UserPreference:
        """Retrieves or initializes user application preferences."""
        pref = self.db.scalars(select(UserPreference).where(UserPreference.user_id == user_id)).first()
        if not pref:
            pref = UserPreference(
                user_id=user_id,
                preferred_language="en",
                theme="light",
                default_aoi="Punjab Central",
                dashboard_layout="STANDARD",
                notification_channels={"in_app": True, "email": False},
            )
            self.db.add(pref)
            self.db.commit()
            self.db.refresh(pref)
        return pref

    def update_preferences(self, user_id: int, payload: UserPreferenceUpdate) -> UserPreference:
        """Updates user personalization settings."""
        pref = self.get_or_create_preferences(user_id)
        if payload.preferred_language is not None:
            pref.preferred_language = payload.preferred_language
        if payload.theme is not None:
            pref.theme = payload.theme
        if payload.default_aoi is not None:
            pref.default_aoi = payload.default_aoi
        if payload.dashboard_layout is not None:
            pref.dashboard_layout = payload.dashboard_layout
        if payload.notification_channels is not None:
            pref.notification_channels = payload.notification_channels
        self.db.commit()
        self.db.refresh(pref)
        logger.info(f"Updated preferences for user ID {user_id}: lang={pref.preferred_language}, theme={pref.theme}")
        return pref

    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        category: str = "SYSTEM",
        priority: str = "NORMAL",
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Creates an in-app system notification for a user."""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            priority=priority,
            action_url=action_url,
            metadata_json=metadata or {},
            read_status=False,
            created_at=datetime.utcnow(),
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def list_user_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        """Queries notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.read_status.is_(False))
        query = query.order_by(desc(Notification.created_at)).limit(limit)
        return list(self.db.scalars(query).all())

    def mark_notification_read(self, notification_id: int, user_id: int) -> Notification:
        """Marks a notification as read."""
        notif = self.db.scalars(
            select(Notification).where(and_(Notification.id == notification_id, Notification.user_id == user_id))
        ).first()
        if not notif:
            raise NotFoundError(message=f"Notification {notification_id} not found.", entity="Notification")
        notif.read_status = True
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def generate_and_save_report(
        self,
        user_id: int,
        report_type: str,
        title: str,
        file_format: str = "CSV",
        organization_id: Optional[int] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> SavedReport:
        """Generates an auditable business intelligence report containing actual queried records."""
        summary_data: Dict[str, Any] = {}

        if report_type == "FARMER_DIRECTORY":
            farmers = self.db.scalars(select(Farmer).limit(100)).all()
            summary_data = {
                "record_count": len(farmers),
                "total_acreage": sum(f.acres for f in farmers),
                "districts": list(set(f.district for f in farmers)),
            }
        elif report_type == "BIOMASS_INVENTORY":
            estimates = self.db.scalars(select(BiomassEstimate).limit(100)).all()
            summary_data = {
                "estimates_count": len(estimates),
                "total_gross_tons": round(sum(e.gross_residue_tons for e in estimates), 2),
                "total_net_usable_tons": round(sum(e.net_usable_biomass_tons for e in estimates), 2),
                "avg_moisture_pct": round(sum(e.moisture_content_pct for e in estimates) / max(1, len(estimates)), 1),
            }
        elif report_type == "DEPLOYMENT_DISPATCH":
            plans = self.db.scalars(select(DeploymentPlan).limit(50)).all()
            summary_data = {
                "plans_count": len(plans),
                "total_biomass_dispatched": round(sum(p.total_biomass_assigned_tons for p in plans), 2),
                "total_route_distance_km": round(sum(p.total_route_distance_km for p in plans), 2),
            }
        elif report_type == "FINANCIAL_PROJECTION":
            scenarios = self.db.scalars(select(FinancialScenario).limit(50)).all()
            summary_data = {
                "scenarios_evaluated": len(scenarios),
                "avg_gross_profit_inr": round(sum(s.gross_profit_inr for s in scenarios) / max(1, len(scenarios)), 2),
                "avg_roi_pct": round(sum(s.roi_pct for s in scenarios) / max(1, len(scenarios)), 1),
            }
        elif report_type == "LCA_IMPACT":
            assessments = self.db.scalars(select(EnvironmentalAssessment).limit(50)).all()
            summary_data = {
                "assessments_count": len(assessments),
                "total_net_avoided_co2e_tons": round(sum(a.net_avoided_co2e_tons for a in assessments), 2),
                "total_carbon_credit_eligible_tons": round(sum(a.carbon_credit_eligible_tons for a in assessments), 2),
            }
        else:
            summary_data = {"status": "CUSTOM_REPORT_GENERATED", "generated_at": datetime.utcnow().isoformat()}

        report = SavedReport(
            user_id=user_id,
            organization_id=organization_id,
            report_type=report_type,
            title=title,
            file_format=file_format.upper(),
            parameters_json=parameters or {},
            summary_data_json=summary_data,
            created_at=datetime.utcnow(),
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        logger.info(f"Generated report '{title}' ({report_type}) for user ID {user_id}.")
        return report

    def list_saved_reports(self, user_id: Optional[int] = None, limit: int = 50) -> List[SavedReport]:
        """Lists generated reports."""
        query = select(SavedReport)
        if user_id is not None:
            query = query.where(SavedReport.user_id == user_id)
        query = query.order_by(desc(SavedReport.created_at)).limit(limit)
        return list(self.db.scalars(query).all())
