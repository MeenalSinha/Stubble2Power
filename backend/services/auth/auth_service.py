"""
Identity, Authentication & Multi-Tenant Organization Service.
Provides cryptographic registration, login, JWT token issuance, session tracking, and tenant isolation.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from backend.models.entities import User, UserSession, Organization, OrganizationMembership, UserPreference
from backend.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, OrganizationCreate
from backend.core.security.password import hash_password, verify_password
from backend.core.security.auth import create_access_token, compute_token_hash
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import AuthenticationError, ConflictError, NotFoundError, ValidationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.security.auth_service")


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, payload: UserRegisterRequest, actor_username: str = "system") -> User:
        """Registers a new identity with salted password hash and default preferences."""
        # Check uniqueness
        existing = self.db.scalars(
            select(User).where(or_(User.username == payload.username, User.email == payload.email))
        ).first()
        if existing:
            if existing.username == payload.username:
                raise ConflictError(message=f"Username '{payload.username}' is already taken.", entity="User")
            raise ConflictError(message=f"Email '{payload.email}' is already registered.", entity="User")

        # Validate role
        valid_roles = [
            "PUBLIC_VISITOR",
            "FARMER",
            "FIELD_OPERATOR",
            "AGRICULTURAL_ANALYST",
            "ENVIRONMENTAL_ANALYST",
            "ORGANIZATION_MANAGER",
            "SYSTEM_ADMINISTRATOR",
        ]
        role = payload.role_name.upper() if payload.role_name else "FARMER"
        if role not in valid_roles:
            raise ValidationError(message=f"Invalid role '{role}'. Must be one of {valid_roles}.", field="role_name")

        user = User(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=role,
            role_name=role,
            organization_id=payload.organization_id,
            farmer_id=payload.farmer_id,
            phone=payload.phone,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        self.db.add(user)
        self.db.flush()

        # Initialize user preference
        pref = UserPreference(
            user_id=user.id,
            preferred_language="en",
            theme="light",
            default_aoi="Punjab Central",
            dashboard_layout="STANDARD",
            notification_channels={"in_app": True, "email": False},
        )
        self.db.add(pref)

        # If organization specified, create membership
        if payload.organization_id:
            membership = OrganizationMembership(
                organization_id=payload.organization_id, user_id=user.id, org_role="MEMBER"
            )
            self.db.add(membership)

        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Registered new user '{user.username}' with role '{role}'.")
        return user

    def authenticate_user(
        self, payload: UserLoginRequest, client_ip: Optional[str] = None, user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Authenticates user credentials and issues signed JWT tokens."""
        user = self.db.scalars(
            select(User).where(or_(User.username == payload.username, User.email == payload.username))
        ).first()

        if not user or not verify_password(payload.password, user.password_hash):
            logger.warning(f"Failed login attempt for username '{payload.username}' from IP {client_ip}.")
            raise AuthenticationError(message="Invalid username or password.")

        if not user.is_active:
            raise AuthenticationError(message="User account is deactivated. Please contact support.")

        role = user.role_name or user.role or "PUBLIC_VISITOR"
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            role=role,
            organization_id=user.organization_id,
            farmer_id=user.farmer_id,
        )

        expire_minutes = int(config_manager.get("security.access_token_expire_minutes"))
        session = UserSession(
            user_id=user.id,
            token_hash=compute_token_hash(access_token),
            ip_address=client_ip,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=expire_minutes),
            is_revoked=False,
        )
        self.db.add(session)
        self.db.commit()

        logger.info(f"User '{user.username}' authenticated successfully. Issued token expiring in {expire_minutes}m.")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in_minutes=expire_minutes,
            user_id=user.id,
            username=user.username,
            role=role,
            organization_id=user.organization_id,
            farmer_id=user.farmer_id,
        )

    def create_organization(self, payload: OrganizationCreate) -> Organization:
        """Creates a new tenant organization."""
        existing = self.db.scalars(
            select(Organization).where(or_(Organization.name == payload.name, Organization.code == payload.code))
        ).first()
        if existing:
            raise ConflictError(
                message=f"Organization '{payload.name}' or code '{payload.code}' already exists.", entity="Organization"
            )

        org = Organization(
            name=payload.name,
            code=payload.code,
            org_type=payload.org_type,
            country=payload.country,
            domain=payload.domain,
            contact_email=payload.contact_email,
            is_active=True,
        )
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        logger.info(f"Created organization '{org.name}' ({org.code}).")
        return org

    def list_organizations(self) -> List[Organization]:
        """Lists active tenant organizations."""
        return list(self.db.scalars(select(Organization).where(Organization.is_active.is_(True))).all())

    def get_organization(self, org_id: int) -> Organization:
        org = self.db.scalars(select(Organization).where(Organization.id == org_id)).first()
        if not org:
            raise NotFoundError(message=f"Organization {org_id} not found.", entity="Organization")
        return org
