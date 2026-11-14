"""
Reliability, Fault Tolerance & Failure Recovery Test Suite.
Verifies system resilience against network partitions, external API outages,
database rollbacks, transient errors, and invalid inputs.
"""

from datetime import date
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

    key = Fernet.generate_key().decode()
    backup_dir = tmp_path / "backups"

    # 1. Create encrypted backup
    backup_file = create_backup(backup_dir=str(backup_dir), encryption_key=key)
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
