"""
Pydantic Schemas for Phase 14 Privacy, Governance, and Audit Logging.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ConsentCreate(BaseModel):
    farmer_id: int
    consent_purpose: str = Field(..., description="BIOMASS_AGGREGATION, SATELLITE_FIRE_CORRELATION, LOGISTICS_DISPATCH, DIRECT_PAYMENT")
    consent_version: str = Field(default="v1.0")
    notes: Optional[str] = None


class ConsentWithdrawRequest(BaseModel):
    consent_id: int
    reason: Optional[str] = None


class ConsentResponse(BaseModel):
    id: int
    farmer_id: int
    user_id: Optional[int] = None
    consent_purpose: str
    consent_version: str
    is_granted: bool
    consent_timestamp: datetime
    withdrawn_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class DataSubjectRequestCreate(BaseModel):
    request_type: str = Field(..., description="ACCESS, CORRECTION, ERASURE, EXPORT")
    details_json: Optional[Dict[str, Any]] = None


class DataSubjectRequestResponse(BaseModel):
    id: int
    user_id: int
    request_type: str
    status: str
    details_json: Dict[str, Any]
    requested_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class DataRetentionPolicyResponse(BaseModel):
    id: int
    data_category: str
    retention_period_days: int
    legal_basis: str
    action_on_expiry: str
    is_active: bool

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    actor_username: str
    organization_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    client_ip: Optional[str] = None
    status_code: int
    details_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityEventResponse(BaseModel):
    id: int
    event_type: str
    severity: str
    user_id: Optional[int] = None
    client_ip: Optional[str] = None
    details_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
