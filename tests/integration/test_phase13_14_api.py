"""
Integration Tests for Phase 13 & Phase 14 API Route Handlers.
Tests Identity, Registration, Login, RBAC, Multi-Tenant Boundaries,
User Preferences, Notifications, Reports, and Privacy Governance.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.models.database import Base
from backend.models.entities import Organization, User, Farmer
from backend.schemas.auth import UserRegisterRequest, UserLoginRequest
from backend.schemas.user_experience import UserPreferenceUpdate, SavedReportCreate
from backend.schemas.privacy import ConsentCreate, DataSubjectRequestCreate
from backend.api.routes import auth, organizations, user_experience, privacy_governance
from backend.core.security.password import hash_password
from backend.core.exceptions.base import ConflictError, AuthenticationError


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Seed baseline Organization and Administrator
    org1 = Organization(name="Ludhiana Agro Coop", code="LDH-COOP", is_active=True)
    org2 = Organization(name="Bathinda Bio-Power Ltd", code="BTI-POWER", is_active=True)
    session.add_all([org1, org2])
    session.commit()
    session.refresh(org1)
    session.refresh(org2)

    admin = User(
        username="superadmin",
        email="admin@stubble2power.gov.in",
        password_hash=hash_password("AdminPass123!"),
        full_name="Platform Administrator",
        role_name="SYSTEM_ADMINISTRATOR",
        is_active=True,
    )
    farmer_rec = Farmer(
        name="Baljit Singh",
        village="Samrala",
        district="Ludhiana",
        state="Punjab",
        acres=15.0,
        stubble_tons=12.0,
        harvest_date=date(2025, 10, 20),
        latitude=30.8300,
        longitude=76.1900,
    )
    session.add_all([admin, farmer_rec])
    session.commit()
    session.refresh(admin)
    session.refresh(farmer_rec)

    yield session, org1, org2, admin, farmer_rec
    session.close()


def mock_request(client_ip="127.0.0.1", user_agent="PytestClient/1.0"):
    req = MagicMock()
    req.client.host = client_ip
    req.headers.get.return_value = user_agent
    return req


def test_auth_registration_and_login_flow(db_session):
    session, org1, _, _, farmer_rec = db_session
    req = mock_request()

    # 1. User Registration
    reg_payload = UserRegisterRequest(
        username="farmer_baljit",
        email="baljit@punjabfarmers.in",
        password="SecurePassword123!",
        full_name="Sardar Baljit Singh",
        role_name="FARMER",
        organization_id=org1.id,
        farmer_id=farmer_rec.id,
        phone="+91-9876500000",
    )
    user = auth.register_user(reg_payload, req, db=session)
    assert user.id is not None
    assert user.username == "farmer_baljit"
    assert user.role_name == "FARMER"

    # 2. Duplicate Registration Rejection
    with pytest.raises(ConflictError):
        auth.register_user(reg_payload, req, db=session)

    # 3. User Login
    login_payload = UserLoginRequest(username="farmer_baljit", password="SecurePassword123!")
    token_data = auth.login_user(login_payload, req, db=session)
    assert token_data.access_token is not None
    assert token_data.role == "FARMER"
    assert token_data.username == "farmer_baljit"

    # 4. Invalid Password Rejection
    with pytest.raises(AuthenticationError):
        auth.login_user(UserLoginRequest(username="farmer_baljit", password="WrongPassword!"), req, db=session)


def test_rbac_roles_endpoint():
    roles = auth.list_roles_and_permissions()
    assert len(roles) >= 7
    role_names = [r.role_name for r in roles]
    assert "SYSTEM_ADMINISTRATOR" in role_names
    assert "FARMER" in role_names
    assert "FIELD_OPERATOR" in role_names


def test_organizations_isolation_routes(db_session):
    session, org1, org2, admin, _ = db_session

    # 1. System Administrator lists all organizations
    all_orgs = organizations.list_organizations(db=session, user=admin)
    assert len(all_orgs) == 2

    # 2. Regular user only sees their own organization
    org_member = User(
        username="member_alpha", email="alpha@coop.in", role_name="ORGANIZATION_MANAGER", organization_id=org1.id
    )
    user_orgs = organizations.list_organizations(db=session, user=org_member)
    assert len(user_orgs) == 1
    assert user_orgs[0].id == org1.id

    # 3. Accessing own organization succeeds
    details = organizations.get_organization_details(org1.id, db=session, user=org_member)
    assert details.id == org1.id

    # 4. Accessing other organization raises 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        organizations.get_organization_details(org2.id, db=session, user=org_member)
    assert exc_info.value.status_code == 403


def test_user_preferences_api(db_session):
    session, _, _, admin, _ = db_session

    # Retrieve initial preferences
    pref = user_experience.get_user_preferences(user=admin, db=session)
    assert pref.preferred_language == "en"

    # Update preferences to Punjabi and dark theme
    updated = user_experience.update_user_preferences(
        UserPreferenceUpdate(preferred_language="pa", theme="dark", default_aoi="Malwa Region"), user=admin, db=session
    )
    assert updated.preferred_language == "pa"
    assert updated.theme == "dark"


def test_reports_generation_api(db_session):
    session, _, _, admin, _ = db_session

    # Generate Report
    rep = user_experience.generate_report(
        SavedReportCreate(report_type="FARMER_DIRECTORY", title="Punjab Harvest Roster", file_format="CSV"),
        user=admin,
        db=session,
    )
    assert rep.id is not None
    assert rep.report_type == "FARMER_DIRECTORY"
    assert rep.summary_data_json["record_count"] >= 1

    # List Reports
    reps = user_experience.list_reports(user=admin, db=session)
    assert len(reps) >= 1


def test_privacy_consent_and_audit_api(db_session):
    session, org1, _, admin, farmer_rec = db_session

    farmer_user = User(
        username="baljit_user",
        email="baljit@farm.in",
        role_name="FARMER",
        organization_id=org1.id,
        farmer_id=farmer_rec.id,
        password_hash=hash_password("Pass123!"),
    )
    session.add(farmer_user)
    session.commit()
    session.refresh(farmer_user)

    # Record consent
    consent = privacy_governance.record_consent(
        ConsentCreate(farmer_id=farmer_rec.id, consent_purpose="BIOMASS_AGGREGATION", consent_version="v1.2"),
        user=farmer_user,
        db=session,
    )
    assert consent.id is not None
    assert consent.is_granted is True

    # Withdraw consent
    withdrawn = privacy_governance.withdraw_consent(consent.id, user=farmer_user, db=session)
    assert withdrawn.is_granted is False

    # Submit Data Subject Request
    dsr = privacy_governance.submit_data_subject_request(
        DataSubjectRequestCreate(request_type="ACCESS", details_json={"query": "export my data"}),
        user=farmer_user,
        db=session,
    )
    assert dsr.id is not None
    assert dsr.status == "SUBMITTED"

    # Admin querying audit logs
    audit_logs = privacy_governance.list_audit_logs(limit=50, user=admin, db=session)
    assert isinstance(audit_logs, list)

    # Admin querying security events
    sec_events = privacy_governance.list_security_events(limit=50, user=admin, db=session)
    assert isinstance(sec_events, list)
