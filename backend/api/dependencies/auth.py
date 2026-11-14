"""
Authentication & Authorization Dependencies for FastAPI.
Enforces cryptographically signed JWT validation, RBAC, tenant isolation, and object-level authorization.
"""

from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.database import get_db
from backend.models.entities import User
from backend.core.security.auth import decode_token
from backend.core.security.rbac import has_permission
from backend.core.exceptions.base import AuthenticationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.security.dependencies")

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme), db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts and validates the bearer token,
    loading the active User entity from the database.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message, headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing user_id identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalars(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated. Contact system administrator."
        )

    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency for endpoints with tiered visibility
    (e.g., public visitors see blurred coordinates, authenticated operators see precise parcels).
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("user_id")
        if user_id:
            user = db.scalars(select(User).where(User.id == user_id, User.is_active.is_(True))).first()
            return user
    except Exception:
        return None
    return None


def require_permission(permission_name: str) -> Callable:
    """Dependency factory checking whether current user possesses the required granular permission."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        user_role = user.role_name or user.role or "PUBLIC_VISITOR"
        if not has_permission(user_role, permission_name):
            logger.warning(
                f"Unauthorized permission check: User '{user.username}' (role {user_role}) "
                f"attempted action requiring '{permission_name}'."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{user_role}' lacks required permission '{permission_name}'.",
            )
        return user

    return dependency


def require_role(allowed_roles: List[str]) -> Callable:
    """Dependency factory restricting access to a specific list of role names."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        user_role = (user.role_name or user.role or "PUBLIC_VISITOR").upper()
        normalized_allowed = [r.upper() for r in allowed_roles]
        if "SYSTEM_ADMINISTRATOR" in user_role or "*" in normalized_allowed:
            return user
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Required role in {allowed_roles}, but user has role '{user_role}'.",
            )
        return user

    return dependency


def verify_organization_access(user: User, organization_id: Optional[int]) -> None:
    """
    Enforces multi-tenant organizational isolation.
    Superusers bypass; standard users can only access resources matching their own organization_id.
    """
    user_role = (user.role_name or user.role or "").upper()
    if user_role == "SYSTEM_ADMINISTRATOR":
        return

    if organization_id is not None and user.organization_id != organization_id:
        logger.warning(
            f"Tenant boundary violation attempt: User '{user.username}' (Org {user.organization_id}) "
            f"attempted to access Org {organization_id} resources."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Cross-organization data access is prohibited."
        )


def verify_resource_ownership(
    user: User, resource_user_id: Optional[int] = None, resource_farmer_id: Optional[int] = None
) -> None:
    """
    Enforces object-level authorization (IDOR prevention).
    Ensures users can only modify/access records they own, unless privileged.
    """
    user_role = (user.role_name or user.role or "").upper()
    if user_role in ["SYSTEM_ADMINISTRATOR", "ORGANIZATION_MANAGER"]:
        return

    if user_role == "FARMER":
        if resource_farmer_id and user.farmer_id != resource_farmer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access another farmer's private records.",
            )
        if resource_user_id and user.id != resource_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Object-level ownership check failed."
            )
