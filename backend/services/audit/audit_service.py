"""
Audit Logging & Security Event Tracking Service.
Provides immutable, tamper-evident audit trail recording for identity, compliance, and governance.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from backend.models.entities import AuditLog, SecurityEvent
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.security.audit")


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        actor_username: str = "anonymous",
        organization_id: Optional[int] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: int = 200,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Persists an immutable audit log entry."""
        log_entry = AuditLog(
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            client_ip=client_ip,
            user_agent=user_agent,
            status_code=status_code,
            details_json=details or {},
            created_at=datetime.utcnow(),
        )
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    def record_security_event(
        self,
        event_type: str,
        severity: str = "LOW",
        user_id: Optional[int] = None,
        client_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        """Records a security anomaly or compliance violation event."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            client_ip=client_ip,
            details_json=details or {},
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        logger.warning(f"Security event recorded [{severity}]: {event_type} from IP {client_ip}")
        return event

    def list_audit_logs(
        self,
        organization_id: Optional[int] = None,
        actor_user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Queries historical audit logs with filtering."""
        query = select(AuditLog)
        if organization_id is not None:
            query = query.where(AuditLog.organization_id == organization_id)
        if actor_user_id is not None:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if action:
            query = query.where(AuditLog.action == action)
        query = query.order_by(desc(AuditLog.created_at)).limit(limit)
        return list(self.db.scalars(query).all())

    def list_security_events(self, limit: int = 100) -> List[SecurityEvent]:
        """Retrieves recent security monitoring events."""
        return list(self.db.scalars(select(SecurityEvent).order_by(desc(SecurityEvent.created_at)).limit(limit)).all())
