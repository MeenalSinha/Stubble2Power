"""
Privacy, Consent & Audit Governance API Routes.
Enforces purpose-bound consent logging, subject rights requests, and security audit querying.
"""

from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import User
from backend.schemas.privacy import (
    ConsentCreate,
    ConsentResponse,
    DataSubjectRequestCreate,
    DataSubjectRequestResponse,
    AuditLogResponse,
    SecurityEventResponse,
)
from backend.services.privacy.privacy_service import PrivacyService
from backend.services.audit.audit_service import AuditService
from backend.api.dependencies.auth import get_current_user, require_role

router = APIRouter(prefix="/api/privacy", tags=["Privacy, Consent & Audit Governance"])


@router.post("/consents", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
def record_consent(payload: ConsentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Records a granular, purpose-bound farmer consent entry."""
    priv_svc = PrivacyService(db)
    return priv_svc.record_consent(
        farmer_id=payload.farmer_id,
        consent_purpose=payload.consent_purpose,
        consent_version=payload.consent_version,
        user_id=user.id,
        notes=payload.notes,
    )


@router.post("/consents/{consent_id}/withdraw", response_model=ConsentResponse)
def withdraw_consent(consent_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Executes consent withdrawal for a specific processing purpose."""
    priv_svc = PrivacyService(db)
    return priv_svc.withdraw_consent(consent_id=consent_id, user_id=user.id)


@router.get("/consents/farmer/{farmer_id}", response_model=List[ConsentResponse])
def list_farmer_consents(farmer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lists purpose-bound consents for a farmer."""
    priv_svc = PrivacyService(db)
    return priv_svc.list_consents_for_farmer(farmer_id)


@router.post("/requests", response_model=DataSubjectRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_data_subject_request(
    payload: DataSubjectRequestCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Submits a formal Data Subject Access/Correction/Erasure Request."""
    priv_svc = PrivacyService(db)
    return priv_svc.submit_subject_request(
        user_id=user.id, request_type=payload.request_type, details=payload.details_json
    )


@router.get("/requests", response_model=List[DataSubjectRequestResponse])
def list_data_subject_requests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lists Data Subject Requests for the authenticated user or all for administrators."""
    priv_svc = PrivacyService(db)
    user_role = (user.role_name or user.role or "").upper()
    if user_role == "SYSTEM_ADMINISTRATOR":
        return priv_svc.list_subject_requests(user_id=None)
    return priv_svc.list_subject_requests(user_id=user.id)


@router.get("/admin/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    limit: int = Query(100, le=500),
    user: User = Depends(require_role(["SYSTEM_ADMINISTRATOR"])),
    db: Session = Depends(get_db),
):
    """Queries immutable system audit trail (Administrator restricted)."""
    audit_svc = AuditService(db)
    return audit_svc.list_audit_logs(limit=limit)


@router.get("/admin/security-events", response_model=List[SecurityEventResponse])
def list_security_events(
    limit: int = Query(100, le=500),
    user: User = Depends(require_role(["SYSTEM_ADMINISTRATOR"])),
    db: Session = Depends(get_db),
):
    """Queries active security monitoring events (Administrator restricted)."""
    audit_svc = AuditService(db)
    return audit_svc.list_security_events(limit=limit)
