"""
Multi-Tenant Organization API Routes.
Enforces organizational boundary creation, member association, and tenant isolation.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.entities import User
from backend.schemas.auth import OrganizationCreate, OrganizationResponse
from backend.services.auth.auth_service import AuthService
from backend.api.dependencies.auth import get_current_user, require_role, verify_organization_access

router = APIRouter(prefix="/api/organizations", tags=["Organizations & Tenants"])


@router.get("/", response_model=List[OrganizationResponse])
def list_organizations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Lists tenant organizations. Regular users see their own organization; administrators see all."""
    auth_svc = AuthService(db)
    all_orgs = auth_svc.list_organizations()
    user_role = (user.role_name or user.role or "").upper()
    if user_role == "SYSTEM_ADMINISTRATOR":
        return all_orgs
    if user.organization_id:
        return [o for o in all_orgs if o.id == user.organization_id]
    return []


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["SYSTEM_ADMINISTRATOR"])),
):
    """Creates a new tenant organization (Administrator restricted)."""
    auth_svc = AuthService(db)
    return auth_svc.create_organization(payload)


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization_details(
    organization_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Retrieves organization details enforcing tenant isolation."""
    verify_organization_access(user, organization_id)
    auth_svc = AuthService(db)
    return auth_svc.get_organization(organization_id)
