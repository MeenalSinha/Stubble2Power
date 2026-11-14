"""
Identity & Authentication API Routes.
Provides user registration, login, profile inspection, and session logout.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import User
from backend.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, TokenResponse,
    UserProfileResponse, RolePermissionResponse
)
from backend.services.auth.auth_service import AuthService
from backend.services.audit.audit_service import AuditService
from backend.core.security.rbac import PERMISSIONS_MATRIX
from backend.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication & Identity"])


@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Registers a new identity with salted password hashing and default personalization."""
    auth_svc = AuthService(db)
    user = auth_svc.register_user(payload)
    
    audit_svc = AuditService(db)
    audit_svc.record_audit(
        action="USER_REGISTRATION",
        resource_type="User",
        resource_id=str(user.id),
        actor_user_id=user.id,
        actor_username=user.username,
        organization_id=user.organization_id,
        client_ip=request.client.host if request.client else None,
        details={"role": user.role_name, "email": user.email}
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticates credentials and returns a cryptographically signed HMAC-SHA256 JWT."""
    auth_svc = AuthService(db)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    try:
        token_res = auth_svc.authenticate_user(payload, client_ip=client_ip, user_agent=user_agent)
        audit_svc = AuditService(db)
        audit_svc.record_audit(
            action="AUTH_LOGIN",
            resource_type="Session",
            actor_user_id=token_res.user_id,
            actor_username=token_res.username,
            organization_id=token_res.organization_id,
            client_ip=client_ip,
            user_agent=user_agent,
            status_code=200
        )
        return token_res
    except Exception as e:
        audit_svc = AuditService(db)
        audit_svc.record_security_event(
            event_type="LOGIN_FAILURE",
            severity="MEDIUM",
            client_ip=client_ip,
            details={"username_attempted": payload.username, "error": str(e)}
        )
        raise


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Retrieves the authenticated principal's profile information."""
    return user


@router.get("/roles", response_model=List[RolePermissionResponse])
def list_roles_and_permissions():
    """Lists system roles and associated granular permissions."""
    result = []
    descriptions = {
        "PUBLIC_VISITOR": "Anonymous or public viewer exploring high-level environmental intelligence.",
        "FARMER": "Agricultural producer managing parcels, crop cycles, and biomass collection.",
        "FIELD_OPERATOR": "Logistics driver or field technician executing collection routes and machinery setups.",
        "AGRICULTURAL_ANALYST": "Domain scientist analyzing regional crop calendars and biomass availability.",
        "ENVIRONMENTAL_ANALYST": "Remote sensing scientist analyzing satellite observations and LCA carbon accounting.",
        "ORGANIZATION_MANAGER": "Manager of an agricultural cooperative or bioenergy cluster enterprise.",
        "SYSTEM_ADMINISTRATOR": "Platform administrator with privileged operational and configuration access."
    }
    for role, perms in PERMISSIONS_MATRIX.items():
        result.append(RolePermissionResponse(
            role_name=role,
            description=descriptions.get(role, "Standard platform role"),
            permissions=sorted(list(perms))
        ))
    return result
