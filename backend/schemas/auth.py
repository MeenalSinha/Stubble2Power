"""
Pydantic Schemas for Identity, Authentication, and RBAC.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., min_length=6, description="Plaintext user password")


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="User email address")
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=150)
    role_name: str = Field(default="FARMER", description="Requested role: FARMER, FIELD_OPERATOR, etc.")
    organization_id: Optional[int] = None
    farmer_id: Optional[int] = None
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user_id: int
    username: str
    role: str
    organization_id: Optional[int] = None
    farmer_id: Optional[int] = None


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role_name: str
    organization_id: Optional[int] = None
    farmer_id: Optional[int] = None
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    code: str = Field(..., min_length=2, max_length=50)
    org_type: str = Field(default="AGRICULTURAL_COOP")
    country: str = Field(default="IND")
    domain: Optional[str] = None
    contact_email: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    code: str
    org_type: str
    country: str
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationMembershipResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    org_role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class RolePermissionResponse(BaseModel):
    role_name: str
    description: str
    permissions: List[str]
