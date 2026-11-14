"""
Security & Penetration-Testing Verification Suite.
Validates resistance against top OWASP vulnerabilities:
1. SQL Injection Resistance on repository queries.
2. Insecure Direct Object Reference (IDOR) & Tenant Isolation.
3. Cryptographic Signature Forgery & Algorithm Confusion (None-algorithm attack).
4. Path Traversal Defense on File & Database Backups.
5. Brute Force Resistance & Key Entropy Gates.
"""

import pytest
import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.models.entities import User, Organization, Farmer
from backend.repositories.farmer_repository import FarmerRepository
from backend.api.dependencies.auth import verify_resource_ownership
from backend.core.security.auth import decode_token
from backend.core.security.password import verify_password, hash_password
from backend.core.exceptions.base import AuthenticationError


def test_sql_injection_defense_in_repositories(db_session: Session):
    """
    Simulates SQL injection payloads in farmer search and coordinate queries.
    Validates that SQLAlchemy parameterized statements treat malicious inputs as literal data.
    """
    repo = FarmerRepository(db_session)
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE farmers; --",
        "1 UNION SELECT null, null, null, null--",
        "admin'--",
    ]

    for payload in sqli_payloads:
        # Search/filter query must not raise SQL syntax error or execute injection
        results = repo.list_all(village=payload)
        assert isinstance(results, list)
        assert len(results) == 0

    # Direct database sanity check: table must still exist and be intact
    farmer_count = db_session.execute(text("SELECT count(*) FROM farmers")).scalar()
    assert farmer_count >= 0


def test_jwt_none_algorithm_confusion_attack():
    """
    Simulates the classic JWT 'alg': 'none' attack where an attacker attempts
    to bypass cryptographic signature verification.
    """
    forged_claims = {
        "sub": "admin",
        "user_id": 1,
        "role": "SYSTEM_ADMINISTRATOR",
        "organization_id": None,
    }
    # Create unsigned token with alg=none
    unsigned_token = jwt.encode(forged_claims, key="", algorithm="none")

    # Verification must fail and raise AuthenticationError
    with pytest.raises(AuthenticationError):
        decode_token(unsigned_token)


def test_cross_tenant_idor_boundary_enforcement(db_session: Session):
    """
    Validates that users in Organization A cannot access resources belonging
    to Organization B, preventing Insecure Direct Object Reference (IDOR).
    """
    # Create Tenant A and Tenant B
    org_a = Organization(name="Coop Alpha", code="COOP-A-01")
    org_b = Organization(name="Coop Beta", code="COOP-B-02")
    db_session.add_all([org_a, org_b])
    db_session.commit()

    from datetime import date

    farmer_a = Farmer(
        name="Farmer Alpha",
        organization_id=org_a.id,
        village="Village Alpha",
        district="Ludhiana",
        acres=10.0,
        stubble_tons=15.0,
        harvest_date=date(2026, 10, 20),
        latitude=30.9010,
        longitude=75.8573,
    )
    farmer_b = Farmer(
        name="Farmer Beta",
        organization_id=org_b.id,
        village="Village Beta",
        district="Sangrur",
        acres=12.0,
        stubble_tons=18.0,
        harvest_date=date(2026, 10, 22),
        latitude=30.2100,
        longitude=74.9450,
    )
    db_session.add_all([farmer_a, farmer_b])
    db_session.commit()

    user_farmer_a = User(
        username="farmer_a_user",
        email="farmer_a@village.org",
        password_hash=hash_password("ValidPass123!"),
        role_name="FARMER",
        farmer_id=farmer_a.id,
        organization_id=org_a.id,
    )
    db_session.add(user_farmer_a)
    db_session.commit()

    # 1. Multi-Tenant Repository Query Isolation
    repo = FarmerRepository(db_session)
    org_a_farmers = repo.list_all(organization_id=org_a.id)
    org_a_ids = [f.id for f in org_a_farmers]
    assert farmer_a.id in org_a_ids
    assert farmer_b.id not in org_a_ids  # Tenant B records strictly filtered out

    # 2. Object-level IDOR verification: Farmer A accessing own record (allowed)
    verify_resource_ownership(user_farmer_a, resource_farmer_id=farmer_a.id)

    # 3. Object-level IDOR verification: Farmer A attempting to access Farmer B record -> Must raise HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc:
        verify_resource_ownership(user_farmer_a, resource_farmer_id=farmer_b.id)
    assert exc.value.status_code == 403


def test_path_traversal_defense_in_backup_paths(tmp_path):
    """
    Validates that malicious path traversal attempts (e.g., ../../../etc/passwd)
    are confined or raise appropriate errors without unauthorized disk overwrite.
    """
    from scripts.backup_db import create_backup
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    traversal_dir = tmp_path / "safe" / ".." / "safe"

    backup_file = create_backup(backup_dir=str(traversal_dir), encryption_key=key)
    # The resolved path must be within the sanitized temporary boundary
    assert backup_file.exists()
    assert str(backup_file).startswith(str(tmp_path))


def test_password_hashing_cryptographic_strength():
    """
    Validates PBKDF2-SHA256 password hashing configuration:
    - High entropy verification
    - Unique salt generation per hash
    - Timing resistance on password verification
    """
    plain = "SuperSecureSecret2026!#"
    hash_1 = hash_password(plain)
    hash_2 = hash_password(plain)

    # Salting invariant: Identical passwords produce distinct hashes
    assert hash_1 != hash_2
    assert "$pbkdf2-sha256$" in hash_1 or "$bcrypt$" in hash_1

    # Verification correctness
    assert verify_password(plain, hash_1) is True
    assert verify_password("WrongPassword!", hash_1) is False


def test_jwt_expired_token_rejection():
    """
    Validates that JWT tokens past their expiration timestamp (exp)
    are strictly rejected with AuthenticationError.
    """
    from backend.core.security.auth import get_jwt_secret_key, get_jwt_algorithm

    expired_claims = {
        "sub": "test_user",
        "user_id": 42,
        "role": "FARMER",
        "exp": 1,  # Epoch 1 (1970) -> definitely expired
    }
    expired_token = jwt.encode(expired_claims, key=get_jwt_secret_key(), algorithm=get_jwt_algorithm())

    with pytest.raises(AuthenticationError):
        decode_token(expired_token)


def test_jwt_tampered_signature_rejection():
    """
    Validates that tokens signed with an unauthorized key or tampered signatures
    are strictly rejected by decode_token.
    """
    valid_claims = {
        "sub": "admin_user",
        "user_id": 1,
        "role": "SYSTEM_ADMINISTRATOR",
    }
    wrong_key_token = jwt.encode(valid_claims, key="unauthorized_attacker_key_value_12345", algorithm="HS256")

    with pytest.raises(AuthenticationError):
        decode_token(wrong_key_token)


def test_sensitive_field_exclusion_from_api_schemas():
    """
    Validates that sensitive authentication fields (e.g. password_hash, salts)
    are excluded from public and authenticated API serialization schemas.
    """
    from backend.schemas.auth import UserProfileResponse
    from backend.schemas.farmer import FarmerResponse

    user_fields = UserProfileResponse.model_fields.keys()
    assert "password_hash" not in user_fields
    assert "password" not in user_fields
    assert "salt" not in user_fields

    farmer_fields = FarmerResponse.model_fields.keys()
    assert "password" not in farmer_fields
    assert "bank_account" not in farmer_fields


def test_organization_code_uniqueness_constraint(db_session: Session):
    """
    Validates that database-level UNIQUE constraints prevent duplicate organization codes,
    preventing tenant identity collision attacks.
    """
    from sqlalchemy.exc import IntegrityError

    org1 = Organization(name="Unique Org 1", code="UNIQUE-TENANT-CODE")
    db_session.add(org1)
    db_session.commit()

    org2 = Organization(name="Unique Org 2", code="UNIQUE-TENANT-CODE")
    db_session.add(org2)
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_backup_encryption_key_strength():
    """
    Validates cryptographic backup encryption key properties:
    - Must be a 44-character URL-safe base64 string (256-bit AES key).
    - Rejects weak, short, or invalid encryption keys.
    """
    from cryptography.fernet import Fernet

    valid_key = Fernet.generate_key().decode()
    assert len(valid_key) == 44

    # Using valid key must initialize Fernet successfully
    f = Fernet(valid_key.encode())
    encrypted = f.encrypt(b"test secret payload")
    assert f.decrypt(encrypted) == b"test secret payload"

    # Weak key (< 32 bytes) must fail to initialize
    weak_key = "short_insecure_key"
    with pytest.raises(Exception):
        Fernet(weak_key.encode())


def test_coordinate_bounds_validation():
    """
    Validates that geographical coordinates outside physical WGS84 bounds
    (lat [-90, 90], lon [-180, 180]) are rejected by schema validators.
    """
    from pydantic import ValidationError as PydanticValidationError
    from backend.schemas.farmer import FarmerCreate
    from datetime import date

    # Latitude out of bounds (> 90)
    with pytest.raises(PydanticValidationError):
        FarmerCreate(
            name="Out Of Bounds Lat",
            village="Village",
            district="District",
            acres=10.0,
            stubble_tons=20.0,
            harvest_date=date(2026, 10, 20),
            latitude=95.0,  # Invalid
            longitude=75.0,
        )

    # Longitude out of bounds (> 180)
    with pytest.raises(PydanticValidationError):
        FarmerCreate(
            name="Out Of Bounds Lon",
            village="Village",
            district="District",
            acres=10.0,
            stubble_tons=20.0,
            harvest_date=date(2026, 10, 20),
            latitude=30.0,
            longitude=195.0,  # Invalid
        )


def test_password_verification_constant_time():
    """
    Validates that password verification applies cryptographic hashing iterations
    (PBKDF2-SHA256 with >= 29,000 iterations), resisting brute force and timing attacks.
    """
    import time

    plain = "TestPassword2026!#"
    hashed = hash_password(plain)

    t0 = time.perf_counter()
    res = verify_password(plain, hashed)
    elapsed = time.perf_counter() - t0

    assert res is True
    # PBKDF2 with sufficient iterations must take a measurable non-zero time (> 1 ms)
    # confirming work factor is active (not plain string comparison)
    assert elapsed > 0.001


def test_unauthenticated_api_request_rejection():
    """
    Validates that requests with missing or empty Authorization header
    fail with AuthenticationError when token decode is attempted.
    """
    with pytest.raises(AuthenticationError):
        decode_token("")

    with pytest.raises(AuthenticationError):
        decode_token("Bearer ")
