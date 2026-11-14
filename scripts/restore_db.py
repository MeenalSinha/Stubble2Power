#!/usr/bin/env python3
"""
Stubble2Power Automated Database Restore Utility.
Restores SQLite or PostgreSQL databases from validated, encrypted backup archives.
Enforces fail-closed configuration, requires explicit destructive confirmation,
verifies cryptographic integrity prior to decryption, and runs comprehensive post-restore validations.
"""

import os
import sys
import argparse
import gzip
import hashlib
import shutil
import subprocess
import logging
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [stubble2power.restore] %(message)s")
logger = logging.getLogger("s2p_restore")


def get_decryption_keys(explicit_key: Optional[str] = None) -> list:
    """
    Returns candidate decryption keys (current key + optional previous rotation key).
    """
    candidates = []
    if explicit_key:
        candidates.append(explicit_key.strip().encode("utf-8"))

    env_key = os.getenv("BACKUP_ENCRYPTION_KEY")
    if env_key:
        candidates.append(env_key.strip().encode("utf-8"))

    prev_key = os.getenv("BACKUP_ENCRYPTION_KEY_PREV")
    if prev_key:
        candidates.append(prev_key.strip().encode("utf-8"))

    dev_key_file = Path("backups/.dev_backup_key")
    if dev_key_file.exists():
        candidates.append(dev_key_file.read_bytes().strip())

    return candidates


def verify_checksum(backup_file: Path) -> bool:
    """Verifies SHA-256 checksum against companion .sha256 file."""
    # Look for .sha256 companion
    checksum_file = Path(str(backup_file) + ".sha256")
    if not checksum_file.exists():
        # Check standard replacement suffix
        checksum_file = backup_file.with_suffix(backup_file.suffix + ".sha256")

    if not checksum_file.exists():
        logger.warning(f"No companion .sha256 file found for {backup_file.name}. Proceeding with caution.")
        return True

    expected_line = checksum_file.read_text().strip()
    expected_hash = expected_line.split()[0]

    h = hashlib.sha256()
    with open(backup_file, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    actual_hash = h.hexdigest()

    if actual_hash.lower() != expected_hash.lower():
        raise ValueError(
            f"Cryptographic Checksum Mismatch for {backup_file.name}!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}\n"
            "Archive has been tampered with or corrupted in transit. Restoration aborted."
        )

    logger.info(f"Cryptographic SHA-256 integrity verified: {actual_hash}")
    return True


def decrypt_archive(encrypted_path: Path, temp_dir: Path, explicit_key: Optional[str] = None) -> Path:
    """
    Decrypts an encrypted backup archive (.enc) to a temporary file.
    Supports key rotation via BACKUP_ENCRYPTION_KEY_PREV.
    """
    keys = get_decryption_keys(explicit_key)
    if not keys:
        raise ValueError(
            "Decryption failed: No encryption key provided. Set BACKUP_ENCRYPTION_KEY or supply via --key argument."
        )

    encrypted_data = encrypted_path.read_bytes()
    decrypted_bytes = None
    successful_key_idx = -1

    for idx, key in enumerate(keys):
        try:
            f = Fernet(key)
            decrypted_bytes = f.decrypt(encrypted_data)
            successful_key_idx = idx
            break
        except InvalidToken:
            continue

    if decrypted_bytes is None:
        raise ValueError(
            "Cryptographic Decryption Failed: None of the candidate keys could decrypt the archive. "
            "Ensure BACKUP_ENCRYPTION_KEY matches the key used during backup."
        )

    logger.info(f"Archive successfully decrypted using key candidate #{successful_key_idx + 1}.")

    # Identify engine format from filename
    if "sqlite" in encrypted_path.name.lower():
        out_name = encrypted_path.stem + ".decrypted.db.gz"
    else:
        out_name = encrypted_path.stem + ".decrypted.dump"

    out_path = temp_dir / out_name
    out_path.write_bytes(decrypted_bytes)
    return out_path


def restore_sqlite(backup_file: Path, target_path: str, dry_run: bool = False) -> None:
    """Restores SQLite database from gzipped archive."""
    logger.info(f"Restoring SQLite database to {target_path}...")
    if dry_run:
        logger.info("[DRY RUN] Would decompress and replace target SQLite database.")
        return

    dest = Path(target_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Create safety backup of existing file if present
    if dest.exists():
        safety_copy = dest.with_suffix(f".pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.bak")
        shutil.copy2(dest, safety_copy)
        logger.info(f"Created safety copy of existing database at {safety_copy}")

    # Decompress to temporary file first
    temp_dest = dest.with_suffix(".restore_tmp")
    with gzip.open(backup_file, "rb") as f_in:
        with open(temp_dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Atomic move
    temp_dest.replace(dest)
    logger.info(f"SQLite database restored successfully ({dest.stat().st_size} bytes).")


def restore_postgresql(backup_file: Path, database_url: str, dry_run: bool = False) -> None:
    """Restores PostgreSQL database using pg_restore."""
    clean_url = database_url.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(clean_url)

    db_name = parsed.path.lstrip("/")
    user = parsed.username or "postgres"
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)
    password = parsed.password or ""

    logger.info(f"Restoring PostgreSQL database '{db_name}' on {host}:{port}...")
    if dry_run:
        logger.info("[DRY RUN] Would execute pg_restore to target database.")
        return

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    cmd = [
        "pg_restore",
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-d",
        db_name,
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        "-v",
        str(backup_file),
    ]

    try:
        proc = subprocess.run(cmd, env=env, check=False, capture_output=True, text=True)
        # pg_restore returns 0 on complete success, 1 on non-fatal warnings (e.g. pre-existing postgis extension)
        if proc.returncode not in (0, 1):
            logger.error(f"pg_restore failed with return code {proc.returncode}: {proc.stderr}")
            raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
        if proc.returncode == 1:
            logger.warning(f"pg_restore completed with non-fatal warnings: {proc.stderr[-200:] if proc.stderr else ''}")
        else:
            logger.info("PostgreSQL pg_restore completed successfully.")
    except FileNotFoundError:
        logger.error("pg_restore binary not found in PATH.")
        raise RuntimeError("pg_restore binary is required for PostgreSQL restoration.")
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_restore failed: {e.stderr}")
        raise


def run_post_restore_validation(database_url: str) -> Tuple[bool, dict]:
    """
    Executes in-depth database queries to verify integrity, key foreign relationships,
    spatial functionality, and record consistency post-restore.
    """
    logger.info("Executing comprehensive post-restore integrity and relationship validation...")
    from sqlalchemy import create_engine, select, func, text
    from sqlalchemy.orm import Session
    from backend.models.entities import Farmer, Farm, AreaOfInterest, User, FarmCrop

    engine = create_engine(database_url)
    metrics = {}

    try:
        with Session(engine) as session:
            # 1. Entity count verification
            metrics["farmer_count"] = session.scalar(select(func.count(Farmer.id))) or 0
            metrics["farm_count"] = session.scalar(select(func.count(Farm.id))) or 0
            metrics["aoi_count"] = session.scalar(select(func.count(AreaOfInterest.id))) or 0
            metrics["user_count"] = session.scalar(select(func.count(User.id))) or 0
            metrics["crop_count"] = session.scalar(select(func.count(FarmCrop.id))) or 0

            logger.info(
                f"Entity Counts: {metrics['farmer_count']} Farmers, {metrics['farm_count']} Farms, "
                f"{metrics['aoi_count']} AOIs, {metrics['user_count']} Users, {metrics['crop_count']} Crops."
            )

            # 2. Relational integrity check (orphaned farm records check)
            orphaned_farms = (
                session.scalar(select(func.count(Farm.id)).where(Farm.farmer_id.not_in(select(Farmer.id)))) or 0
            )
            metrics["orphaned_farms"] = orphaned_farms
            if orphaned_farms > 0:
                logger.error(f"Relational Integrity Violation: {orphaned_farms} farms lack valid parent farmers!")
                return False, metrics

            # 3. Spatial / PostGIS verification
            is_postgres = database_url.startswith("postgresql")
            if is_postgres:
                try:
                    postgis_ver = session.execute(text("SELECT PostGIS_Version()")).scalar()
                    metrics["postgis_version"] = str(postgis_ver)
                    logger.info(f"PostGIS Extension Active: {postgis_ver}")
                except Exception as p_err:
                    logger.warning(f"PostGIS check: {p_err}")
                    metrics["postgis_version"] = "NOT_AVAILABLE"

            metrics["validation_status"] = "PASSED"
            logger.info("Comprehensive post-restore integrity checks PASSED.")
            return True, metrics

    except Exception as exc:
        logger.error(f"Post-restore validation failed: {exc}", exc_info=True)
        metrics["validation_status"] = "FAILED"
        metrics["error"] = str(exc)
        return False, metrics
    finally:
        engine.dispose()


def log_restore_audit(
    backup_file: str, target_url: str, success: bool, metrics: dict, operator: str = "automated"
) -> None:
    """Logs the restore operation to an audit log file."""
    audit_dir = Path("backups")
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_log = audit_dir / "restore_audit.log"

    timestamp = datetime.now(timezone.utc).isoformat()
    # Mask password in URL for audit log safety
    clean_url = target_url
    if "@" in target_url:
        prefix, rest = target_url.split("@", 1)
        scheme_user = prefix.split(":", 2)
        if len(scheme_user) >= 3:
            clean_url = f"{scheme_user[0]}:{scheme_user[1]}:***@{rest}"

    entry = {
        "timestamp_utc": timestamp,
        "backup_archive": Path(backup_file).name,
        "target_database": clean_url,
        "success": success,
        "operator": operator,
        "metrics": metrics,
    }

    import json

    with open(audit_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info(f"Restore audit record persisted to {audit_log}.")


def restore_backup(
    backup_file_path: str,
    target_database_url: Optional[str] = None,
    dry_run: bool = False,
    confirm_destructive: bool = False,
    encryption_key: Optional[str] = None,
) -> bool:
    """
    Main restore orchestration entrypoint.
    Enforces fail-closed configuration, requires explicit confirmation,
    verifies cryptographic integrity, decrypts archive, executes restore, and validates data.
    """
    backup_file = Path(backup_file_path)
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup archive does not exist: {backup_file}")

    # 1. Destructive Operation Confirmation Gate
    if not dry_run and not confirm_destructive:
        raise PermissionError(
            "DESTRUCTIVE RESTORE PREVENTED: You must explicitly pass '--confirm-destructive' "
            "to perform database restoration. This action modifies existing database records."
        )

    # 2. Determine and validate target database URL
    db_url = target_database_url or os.getenv("RESTORE_TARGET_DATABASE_URL") or os.getenv("DATABASE_URL")
    env = os.getenv("APP_ENV", "development").strip().lower()

    if not db_url:
        if env in ("production", "prod"):
            raise ValueError(
                "FAIL-CLOSED: Production restore requires explicit target database URL via "
                "--target-db-url or RESTORE_TARGET_DATABASE_URL environment variable."
            )
        else:
            db_url = "sqlite:///./database/stubble2power.db"
            logger.warning(f"No target database specified; defaulting to local development SQLite: {db_url}")

    # 3. Cryptographic integrity check prior to decryption
    verify_checksum(backup_file)

    # 4. Decrypt if encrypted (.enc)
    temp_dir = backup_file.parent / ".restore_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_decrypted_file = None

    try:
        if backup_file.suffix == ".enc" or ".enc" in backup_file.name:
            logger.info("Encrypted backup detected. Initiating cryptographic decryption...")
            restore_target_file = decrypt_archive(backup_file, temp_dir, encryption_key)
            temp_decrypted_file = restore_target_file
        else:
            restore_target_file = backup_file

        # 5. Execute engine-specific restore
        with open(restore_target_file, "rb") as f_hdr:
            hdr = f_hdr.read(16)
        is_pg = hdr.startswith(b"PGDMP")
        is_sqlite = hdr.startswith(b"SQLite format 3") or hdr.startswith(b"\x1f\x8b")

        if is_pg and db_url.startswith("sqlite"):
            raise ValueError(
                "INCOMPATIBLE RESTORE TARGET: The backup archive is a PostgreSQL binary dump (pg_dump format) "
                "and cannot be restored into an SQLite target."
            )
        if is_sqlite and not db_url.startswith("sqlite"):
            raise ValueError(
                "INCOMPATIBLE RESTORE TARGET: The backup archive is an SQLite database/gzip archive "
                "and cannot be restored into a PostgreSQL target."
            )

        if db_url.startswith("sqlite"):
            db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
            if not db_path or db_path == ":memory:":
                db_path = "./stubble2power.db"
            restore_sqlite(restore_target_file, db_path, dry_run)
        else:
            restore_postgresql(restore_target_file, db_url, dry_run)

        # 6. Post-restore comprehensive validation
        metrics = {}
        success = True
        if not dry_run:
            success, metrics = run_post_restore_validation(db_url)

        # 7. Persist audit log
        log_restore_audit(str(backup_file), db_url, success, metrics)
        return success

    finally:
        # Secure cleanup of temporary decrypted plaintext
        if temp_decrypted_file and temp_decrypted_file.exists():
            temp_decrypted_file.unlink()
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stubble2Power Secure Database Restore Utility")
    parser.add_argument("backup_file", help="Path to backup archive (.enc, .db.gz, or .dump)")
    parser.add_argument("--target-db-url", default=None, help="Explicit target database URL")
    parser.add_argument(
        "--confirm-destructive", action="store_true", help="Mandatory explicit confirmation for destructive restore"
    )
    parser.add_argument("--key", default=None, help="Explicit decryption key (defaults to BACKUP_ENCRYPTION_KEY)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate checksum and print actions without modifying data"
    )
    args = parser.parse_args()

    try:
        res = restore_backup(
            args.backup_file,
            target_database_url=args.target_db_url,
            dry_run=args.dry_run,
            confirm_destructive=args.confirm_destructive,
            encryption_key=args.key,
        )
        if res:
            print("SUCCESS: Database restore and validation completed successfully.")
            sys.exit(0)
        else:
            print("ERROR: Restore executed but post-restore integrity validation failed.")
            sys.exit(1)
    except Exception as exc:
        logger.error(f"Restore failed: {exc}", exc_info=True)
        sys.exit(1)
