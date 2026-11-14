"""
Unit Tests for Phase 14: Security, Authentication, RBAC, and Privacy Governance.
Tests cryptographic password hashing, JWT lifecycle, RBAC enforcement,
tenant boundary isolation, audit logging, and geospatial privacy blurring.
"""

import pytest
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.entities import Base, User, Organization
from backend.core.security.password import hash_password, verify_password
from backend.core.security.auth import create_access_token, decode_token
from backend.core.security.rbac import has_permission, assert_permission
from backend.services.audit.audit_service import AuditService
from backend.services.privacy.privacy_service import PrivacyService
from backend.api.dependencies.auth import verify_organization_access, verify_resource_ownership
from backend.core.exceptions.base import AuthenticationError, AuthorizationError
from fastapi import HTTPException


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_password_hashing_and_verification():
    raw_pass = "P@ssword2026!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_creation_and_decoding():
    token = create_access_token(
        user_id=42,
        username="test_analyst",
        role="ENVIRONMENTAL_ANALYST",
        organization_id=1,
        farmer_id=None,
        expires_delta=timedelta(minutes=15),
    )
    assert token is not None
    payload = decode_token(token)
    assert payload["sub"] == "test_analyst"
    assert payload["user_id"] == 42
    assert payload["role"] == "ENVIRONMENTAL_ANALYST"
    assert payload["organization_id"] == 1
    assert payload["type"] == "access"


def test_expired_jwt_token_rejection():
    expired_token = create_access_token(
        user_id=1, username="expired_user", role="PUBLIC_VISITOR", expires_delta=timedelta(seconds=-10)
    )
    with pytest.raises(AuthenticationError):
        decode_token(expired_token)


def test_rbac_permission_matrix():
    # Public Visitor
    assert has_permission("PUBLIC_VISITOR", "fire:view_public") is True
    assert has_permission("PUBLIC_VISITOR", "farm:view_org") is False
    assert has_permission("PUBLIC_VISITOR", "admin:config") is False

    # Farmer
    assert has_permission("FARMER", "farm:view_own") is True
    assert has_permission("FARMER", "harvest:log_own") is True
    assert has_permission("FARMER", "deployment:plan_org") is False

    # Organization Manager
    assert has_permission("ORGANIZATION_MANAGER", "farm:view_org") is True
    assert has_permission("ORGANIZATION_MANAGER", "finance:view_org") is True
    assert has_permission("ORGANIZATION_MANAGER", "admin:audit") is False

    # System Administrator (Superuser wildcard)
    assert has_permission("SYSTEM_ADMINISTRATOR", "admin:audit") is True
    assert has_permission("SYSTEM_ADMINISTRATOR", "any:custom:action") is True

    # Assertion check
    assert_permission("FARMER", "farm:view_own")
    with pytest.raises(AuthorizationError):
        assert_permission("FARMER", "admin:audit")


def test_tenant_organization_isolation(db_session):
    org1 = Organization(name="Coop Alpha", code="ALPHA")
    org2 = Organization(name="Coop Beta", code="BETA")
    db_session.add_all([org1, org2])
    db_session.flush()

    user_alpha = User(username="user_a", email="a@alpha.com", role_name="ORGANIZATION_MANAGER", organization_id=org1.id)
    admin_user = User(
        username="super_admin", email="admin@root.com", role_name="SYSTEM_ADMINISTRATOR", organization_id=None
    )

    # User in Org Alpha should be permitted to access Org Alpha
    verify_organization_access(user_alpha, org1.id)

    # User in Org Alpha attempting to access Org Beta should be denied (403)
    with pytest.raises(HTTPException) as exc_info:
        verify_organization_access(user_alpha, org2.id)
    assert exc_info.value.status_code == 403

    # Superadmin can access any organization
    verify_organization_access(admin_user, org1.id)
    verify_organization_access(admin_user, org2.id)


def test_object_level_ownership_enforcement():
    farmer_user = User(id=10, username="farmer_1", email="f1@punjab.in", role_name="FARMER", farmer_id=101)

    # Farmer accessing own resource
    verify_resource_ownership(farmer_user, resource_farmer_id=101)

    # Farmer accessing another farmer's resource raises 403
    with pytest.raises(HTTPException) as exc_info:
        verify_resource_ownership(farmer_user, resource_farmer_id=102)
    assert exc_info.value.status_code == 403


def test_geospatial_location_privacy_blurring(db_session):
    priv_svc = PrivacyService(db_session)
    exact_lat = 30.705623
    exact_lon = 76.222289

    # Public visitor sees blurred coordinates (2 decimal places ~1.1km blur)
    pub_lat, pub_lon, is_blurred = priv_svc.filter_location_privacy(exact_lat, exact_lon, viewer_role="PUBLIC_VISITOR")
    assert is_blurred is True
    assert pub_lat == 30.71
    assert pub_lon == 76.22

    # Authorized Field Operator receives unblurred precision
    op_lat, op_lon, is_blurred = priv_svc.filter_location_privacy(exact_lat, exact_lon, viewer_role="FIELD_OPERATOR")
    assert is_blurred is False
    assert op_lat == exact_lat
    assert op_lon == exact_lon


def test_guaranteed_spatial_obfuscation_annulus(db_session):
    """
    Validates that annular spatial obfuscation mathematically guarantees a minimum
    displacement distance >= 1.0 km and maximum <= 2.5 km, mitigating cadastral
    re-identification for all locations.

    Privacy model: probabilistic location privacy with guaranteed 1.0 km minimum
    displacement. Population-level k-anonymity depends on local farm density:
    k ≈ 6–16 at 1.0 km radius; k ≈ 39–98 at 2.5 km radius (Punjab intensive zones,
    2–5 farms/km²). k is NOT guaranteed >= 80 uniformly.

    Tolerances account for WGS84 metric tensor approximation at Punjab latitudes (~30°N).
    """
    from backend.services.geospatial.service import GeospatialService

    priv_svc = PrivacyService(db_session)
    exact_lat = 30.705623
    exact_lon = 76.222289

    # --- Test 1: 1000-iteration displacement bounds (unseeded = fresh random per call) ---
    MIN_KM = 0.995   # 1.0 km with WGS84 metric tensor tolerance at 30°N
    MAX_KM = 2.555   # 2.5 km with WGS84 metric tensor tolerance at 30°N

    for _ in range(1000):
        obf_lat, obf_lon, _r_km = priv_svc.apply_spatial_obfuscation(
            exact_lat, exact_lon, min_radius_km=1.0, max_radius_km=2.5
            # No seed → fresh random.Random() per call
        )
        actual_distance = GeospatialService.haversine_distance(exact_lat, exact_lon, obf_lat, obf_lon)
        # Guaranteed displacement lower bound (1.0 km minimum)
        assert actual_distance >= MIN_KM, (
            f"Privacy invariant violated: displacement {actual_distance:.4f} km < {MIN_KM} km minimum"
        )
        # Guaranteed displacement upper bound (2.5 km maximum)
        assert actual_distance <= MAX_KM, (
            f"Privacy invariant violated: displacement {actual_distance:.4f} km > {MAX_KM} km maximum"
        )

    # --- Test 2: Deterministic seed path still satisfies bounds (for CI reproducibility) ---
    for seed in range(50):
        obf_lat, obf_lon, _r_km = priv_svc.apply_spatial_obfuscation(
            exact_lat, exact_lon, min_radius_km=1.0, max_radius_km=2.5, seed=seed
        )
        actual_distance = GeospatialService.haversine_distance(exact_lat, exact_lon, obf_lat, obf_lon)
        assert actual_distance >= MIN_KM, f"Seeded obfuscation below minimum: {actual_distance:.4f} km (seed={seed})"
        assert actual_distance <= MAX_KM, f"Seeded obfuscation above maximum: {actual_distance:.4f} km (seed={seed})"

    # --- Test 3: Repeated-query independence (triangulation resistance) ---
    # Two calls with identical input coordinates must return DIFFERENT displaced coordinates.
    # This confirms that unseeded calls draw fresh OS entropy, preventing triangulation.
    obf_lat_1, obf_lon_1, _ = priv_svc.apply_spatial_obfuscation(
        exact_lat, exact_lon, min_radius_km=1.0, max_radius_km=2.5
    )
    obf_lat_2, obf_lon_2, _ = priv_svc.apply_spatial_obfuscation(
        exact_lat, exact_lon, min_radius_km=1.0, max_radius_km=2.5
    )
    assert (obf_lat_1, obf_lon_1) != (obf_lat_2, obf_lon_2), (
        "Repeated-query triangulation vulnerability: two unseed calls returned identical "
        "displaced coordinates, indicating a fixed/shared RNG state."
    )


def test_audit_logging_and_security_events(db_session):
    audit_svc = AuditService(db_session)
    log = audit_svc.record_audit(
        action="TEST_ACTION",
        resource_type="Farm",
        resource_id="105",
        actor_username="test_user",
        status_code=200,
        details={"parcel_acres": 25.0},
    )
    assert log.id is not None
    assert log.action == "TEST_ACTION"

    sec_event = audit_svc.record_security_event(
        event_type="UNAUTHORIZED_ACCESS_ATTEMPT",
        severity="HIGH",
        client_ip="192.168.1.100",
        details={"attempted_url": "/api/admin/audit-logs"},
    )
    assert sec_event.id is not None
    assert sec_event.severity == "HIGH"

    logs = audit_svc.list_audit_logs(action="TEST_ACTION")
    assert len(logs) == 1
    events = audit_svc.list_security_events()
    assert len(events) == 1
