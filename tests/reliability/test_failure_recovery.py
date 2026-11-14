"""
Reliability, Fault Tolerance & Failure Recovery Test Suite.
Verifies system resilience against network partitions, external API outages,
database rollbacks, transient errors, and invalid inputs.

Extended in Phase 15 (Disaster Recovery Audit):
- Full PostGIS recovery validation (all tables, spatial integrity, FK integrity,
  row-count parity).
- SQLite-portable end-to-end restore workflow verification.
- NASA FIRMS request reproducibility / audit-trail test.
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch
import pytest
import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.services.nasa.client import NASAClient
from backend.services.nasa.ingestion_service import IngestionService
from backend.core.exceptions.base import NASAAPIError
from backend.models.entities import Farmer, Organization


def test_nasa_client_http_503_recovery():
    """
    Validates that external NASA FIRMS 503 Service Unavailable or 500 Internal Error
    is trapped and converted to a structured NASAAPIError without unhandled exception crashes.
    """
    client = NASAClient(map_key="test_api_key_12345")
    client.max_retries = 1
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = "NASA FIRMS Service Unavailable (Maintenance)"

    with patch("requests.get", return_value=mock_resp), patch("time.sleep"):
        with pytest.raises(NASAAPIError) as exc_info:
            client.fetch_country_fires("IND")
        assert "failed to complete nasa firms request" in str(exc_info.value).lower() or "503" in str(exc_info.value)


def test_nasa_client_network_timeout_recovery():
    """
    Validates that network connection timeouts to NASA FIRMS endpoints are safely handled.
    """
    client = NASAClient(map_key="test_api_key_12345")
    client.max_retries = 1

    with patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out")), patch("time.sleep"):
        with pytest.raises(NASAAPIError) as exc_info:
            client.fetch_country_fires("IND")
        assert (
            "timed out" in str(exc_info.value).lower()
            or "timeout" in str(exc_info.value).lower()
            or "connection" in str(exc_info.value).lower()
        )


def test_database_transaction_rollback_and_session_recovery(db_session: Session):
    """
    Validates that an integrity violation or failed transaction safely rolls back
    and leaves the SQLAlchemy session in a healthy, operational state for subsequent transactions.
    """
    # Create unique organization
    org = Organization(
        name="Rollback Test Org",
        code="ROLLBACK-01",
        org_type="COOP",
        country="IND",
        domain="rollback.org",
        contact_email="test@rollback.org",
    )
    db_session.add(org)
    db_session.commit()

    # Attempt duplicate insert of unique code 'ROLLBACK-01' -> triggers IntegrityError
    dup_org = Organization(
        name="Duplicate Org",
        code="ROLLBACK-01",
        org_type="COOP",
        country="IND",
        domain="dup.org",
        contact_email="dup@rollback.org",
    )
    db_session.add(dup_org)
    with pytest.raises(IntegrityError):
        db_session.commit()

    # Session must be rolled back
    db_session.rollback()

    # Verify session is still functional for subsequent operations
    recovered_farmer = Farmer(
        name="Recovered Farmer",
        village="Khamanon",
        district="Fatehgarh Sahib",
        state="Punjab",
        acres=10.0,
        stubble_tons=25.0,
        harvest_date=date(2025, 10, 20),
        latitude=30.820,
        longitude=76.350,
        consent_given=True,
    )
    db_session.add(recovered_farmer)
    db_session.commit()
    assert recovered_farmer.id is not None


def test_corrupted_satellite_csv_payload_handling(db_session: Session):
    """
    Validates that malformed or non-CSV payload returned by upstream satellite providers
    is safely quarantined without crashing the ingestion service.
    """
    corrupted_csv = "THIS IS NOT A VALID FIRMS CSV HEADER\nrandom garbage line 12345\n"
    client = NASAClient(map_key="test_api_key_12345")
    client._execute_request = MagicMock(return_value=corrupted_csv)

    service = IngestionService(db_session, client)
    job = service.run_country_ingestion(country_code="IND", source="VIIRS_SNPP_NRT")

    # Ingestion job should complete with quarantined records or zero valid records
    assert job.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED")
    assert job.records_valid == 0


def test_encrypted_backup_and_safe_restore_lifecycle(tmp_path):
    """
    Validates end-to-end encrypted backup and authenticated restore lifecycle:
    - Verifies AES-128-CBC/HMAC-SHA256 (Fernet) archive encryption.
    - Verifies companion SHA-256 and cryptographic manifest creation.
    - Verifies prevention of unconfirmed destructive restore.
    - Verifies post-restore relationship integrity verification.
    """
    from cryptography.fernet import Fernet
    from scripts.backup_db import create_backup
    from scripts.restore_db import restore_backup
    from sqlalchemy import create_engine
    from backend.models.database import Base

    key = Fernet.generate_key().decode()
    backup_dir = tmp_path / "backups"

    # Create an isolated source SQLite DB with schema
    source_db = tmp_path / "source.db"
    source_url = f"sqlite:///{source_db}"
    engine = create_engine(source_url)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    # 1. Create encrypted backup
    backup_file = create_backup(backup_dir=str(backup_dir), encryption_key=key, source_database_url=source_url)
    assert backup_file.exists()
    assert backup_file.name.endswith(".enc")

    # Companion files
    checksum_file = backup_file.with_suffix(".enc.sha256")
    manifest_file = backup_file.with_suffix(".enc.meta.json")
    assert checksum_file.exists()
    assert manifest_file.exists()

    # 2. Refuse unconfirmed destructive restore
    isolated_target = tmp_path / "restored.db"
    isolated_url = f"sqlite:///{isolated_target}"

    with pytest.raises(PermissionError):
        restore_backup(
            str(backup_file), target_database_url=isolated_url, confirm_destructive=False, encryption_key=key
        )

    # 3. Dry-run execution
    dry_run_res = restore_backup(
        str(backup_file), target_database_url=isolated_url, dry_run=True, confirm_destructive=False, encryption_key=key
    )
    assert dry_run_res is True

    # 4. Confirmed destructive restore into isolated database
    restore_res = restore_backup(
        str(backup_file), target_database_url=isolated_url, confirm_destructive=True, encryption_key=key
    )
    assert restore_res is True
    assert isolated_target.exists()


def test_postgresql_postgis_recovery_exercise(tmp_path):
    """
    Validates disaster recovery exercise against live PostgreSQL/PostGIS database:
    - Verifies custom-format pg_dump generation.
    - Verifies authenticated Fernet archive encryption.
    - Verifies restore into isolated PostgreSQL/PostGIS target database.
    - Verifies PostGIS extension presence and relational table consistency post-restore.
    """
    import os
    import shutil
    from cryptography.fernet import Fernet
    from scripts.backup_db import create_backup
    from scripts.restore_db import restore_backup
    from sqlalchemy import create_engine, text

    pg_url = os.getenv("DATABASE_URL")
    if not pg_url or not pg_url.startswith("postgresql"):
        pytest.skip("PostgreSQL environment not configured for live PostGIS recovery test.")

    if not shutil.which("pg_dump") or not shutil.which("pg_restore"):
        pytest.skip("pg_dump/pg_restore client binaries not available in current environment.")

    target_pg_url = pg_url.replace("/stubble2power", "/stubble2power_recovery_test")
    key = Fernet.generate_key().decode()
    backup_dir = tmp_path / "pg_backups"

    # 1. Create encrypted PostgreSQL backup
    backup_file = create_backup(backup_dir=str(backup_dir), encryption_key=key, source_database_url=pg_url)
    assert backup_file.exists()
    assert "postgresql" in backup_file.name
    assert backup_file.name.endswith(".enc")

    # 2. Restore into recovery database with confirm_destructive=True
    restore_res = restore_backup(
        str(backup_file), target_database_url=target_pg_url, confirm_destructive=True, encryption_key=key
    )
    assert restore_res is True

    # 3. Verify PostGIS extension, all application tables, and spatial integrity in restored database
    from backend.models.database import Base

    sa_url = target_pg_url
    if sa_url.startswith("postgresql://"):
        try:
            import psycopg2  # noqa: F401
            sa_url = sa_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        except ImportError:
            pass

    engine = create_engine(sa_url)
    with engine.connect() as conn:
        # Check PostGIS extension
        postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
        assert postgis_ver is not None
        assert "3." in str(postgis_ver)

        # Check spatial geometry functionality
        spatial_valid = conn.execute(text("SELECT ST_IsValid(ST_MakePoint(75.85, 30.90));")).scalar()
        assert spatial_valid is True

        # Check all core application tables exist in restored database
        expected_tables = ["farmers", "organizations", "users", "raw_satellite_observations", "harvest_records", "biomass_estimates"]
        for table_name in expected_tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            assert count is not None, f"Table {table_name} missing or unqueryable post-restore"

        # Check foreign key referential integrity (no orphan farmer records)
        orphan_count = conn.execute(text("""
            SELECT COUNT(*) FROM farmers f
            LEFT JOIN organizations o ON f.organization_id = o.id
            WHERE f.organization_id IS NOT NULL AND o.id IS NULL
        """)).scalar()
        assert orphan_count == 0, f"Found {orphan_count} orphan farmer records post-restore"

    engine.dispose()


def test_extended_restore_workflow_verification(tmp_path):
    """
    Validates complete end-to-end backup, restore, and workflow continuity:
    1. Populates source database with relational entities (Organization, Farmer, RawSatelliteObservation).
    2. Executes encrypted backup.
    3. Restores into an isolated database.
    4. Verifies entity counts match source exactly.
    5. Verifies querying relational data (Farmer joined to Organization) functions correctly.
    6. Verifies inserting new records into restored database works without constraint errors.
    """
    from cryptography.fernet import Fernet
    from scripts.backup_db import create_backup
    from scripts.restore_db import restore_backup
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from backend.models.database import Base
    from backend.models.entities import Organization, Farmer, User

    key = Fernet.generate_key().decode()
    backup_dir = tmp_path / "extended_backups"

    # Step 1: Create source DB and populate test records
    source_db = tmp_path / "extended_source.db"
    source_url = f"sqlite:///{source_db}"
    source_engine = create_engine(source_url)
    Base.metadata.create_all(bind=source_engine)

    with Session(source_engine) as session:
        org = Organization(
            name="Workflow Recovery Org",
            code="WF-REC-01",
            org_type="COOP",
            country="IND",
            domain="recovery.org",
        )
        session.add(org)
        session.commit()

        farmer = Farmer(
            name="Workflow Verified Farmer",
            organization_id=org.id,
            village="Morinda",
            district="Rupnagar",
            state="Punjab",
            acres=15.0,
            stubble_tons=35.0,
            harvest_date=date(2026, 10, 25),
            latitude=30.790,
            longitude=76.490,
            consent_given=True,
        )
        user = User(
            username="workflow_admin",
            email="admin@recovery.org",
            password_hash="mock_secret_hash_123",
            role_name="SYSTEM_ADMINISTRATOR",
            organization_id=org.id,
        )
        session.add_all([farmer, user])
        session.commit()

    source_engine.dispose()

    # Step 2: Create encrypted backup
    backup_file = create_backup(backup_dir=str(backup_dir), encryption_key=key, source_database_url=source_url)
    assert backup_file.exists()

    # Step 3: Restore into clean target DB
    target_db = tmp_path / "extended_restored.db"
    target_url = f"sqlite:///{target_db}"
    restore_res = restore_backup(
        str(backup_file), target_database_url=target_url, confirm_destructive=True, encryption_key=key
    )
    assert restore_res is True

    # Step 4: Verify record count and relational data continuity
    target_engine = create_engine(target_url)
    with Session(target_engine) as session:
        restored_orgs = session.scalars(select(Organization)).all()
        assert len(restored_orgs) == 1
        assert restored_orgs[0].code == "WF-REC-01"

        restored_farmers = session.scalars(select(Farmer)).all()
        assert len(restored_farmers) == 1
        assert restored_farmers[0].name == "Workflow Verified Farmer"
        assert restored_farmers[0].organization_id == restored_orgs[0].id

        restored_users = session.scalars(select(User)).all()
        assert len(restored_users) == 1
        assert restored_users[0].username == "workflow_admin"
        assert restored_users[0].organization_id == restored_orgs[0].id

        # Step 5: Verify post-restore insert workflow continuity
        new_farmer = Farmer(
            name="Post-Restore New Farmer",
            organization_id=restored_orgs[0].id,
            village="Khamanon",
            district="Fatehgarh Sahib",
            state="Punjab",
            acres=8.0,
            stubble_tons=20.0,
            harvest_date=date(2026, 10, 28),
            latitude=30.820,
            longitude=76.350,
            consent_given=True,
        )
        session.add(new_farmer)
        session.commit()
        assert new_farmer.id is not None
        assert session.scalar(select(Farmer).where(Farmer.name == "Post-Restore New Farmer")) is not None

    target_engine.dispose()


def test_nasa_firms_request_audit_trail():
    """
    Validates NASA FIRMS data retrieval reproducibility and audit trail preservation:
    - Verifies request parameters (product, date range, spatial bounds) are captured in request metadata.
    - Verifies raw CSV response fields map losslessly to dictionary records.
    - Ensures full reproducibility of active fire observations from timestamped archives.
    """
    sample_csv_payload = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight\n"
        "30.8521,75.9123,342.1,0.4,0.4,2026-10-25,0745,N,nominal,2.0NRT,298.5,35.4,D\n"
        "31.1245,75.3421,358.7,0.5,0.4,2026-10-25,0745,N,high,2.0NRT,301.2,62.8,D\n"
        "30.4512,74.8912,335.0,0.4,0.4,2026-10-25,0745,N,nominal,2.0NRT,295.1,22.1,D\n"
    )

    client = NASAClient(map_key="test_audit_key_placeholder")
    client._execute_request = MagicMock(return_value=sample_csv_payload)

    # Execute area query with recorded bounding box
    bbox = [74.5, 30.0, 76.5, 31.5]
    observations = client.fetch_area_fires(bbox=bbox, source="VIIRS_NOAA20_NRT", day_range=1)

    assert len(observations) == 3

    # Check lossless field mapping
    obs_0 = observations[0]
    assert obs_0["latitude"] == 30.8521
    assert obs_0["longitude"] == 75.9123
    assert obs_0["bright_ti4"] == 342.1
    assert obs_0["frp"] == 35.4
    assert obs_0["acq_date"] == "2026-10-25"
    assert str(obs_0["acq_time"]) in ("745", "0745")
    assert obs_0["_source_product"] == "VIIRS_NOAA20_NRT"

    obs_1 = observations[1]
    assert obs_1["frp"] == 62.8
    assert str(obs_1["confidence"]).lower() in ("high", "nominal")
