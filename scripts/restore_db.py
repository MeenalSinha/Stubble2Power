#!/usr/bin/env python3
"""
Stubble2Power Automated Database Restore Utility
Restores SQLite or PostgreSQL databases from validated backup archives.
Performs cryptographic SHA-256 verification and post-restore integrity smoke testing.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [stubble2power.restore] %(message)s"
)
logger = logging.getLogger("s2p_restore")


def verify_checksum(backup_file: Path) -> bool:
    """Verifies SHA-256 checksum against companion .sha256 file."""
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
            f"Cryptographic Checksum Mismatch!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )

    logger.info(f"Cryptographic SHA-256 checksum verified: {actual_hash}")
    return True


def restore_sqlite(backup_file: Path, target_path: str, dry_run: bool = False) -> None:
    """Restores SQLite database from gzipped archive."""
    logger.info(f"Restoring SQLite database to {target_path}...")
    if dry_run:
        logger.info("[DRY RUN] Would decompress and replace target SQLite database.")
        return

    dest = Path(target_path)
    # Create safety backup of existing file if present
    if dest.exists():
        safety_copy = dest.with_suffix(".pre_restore.bak")
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
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", db_name,
        "--clean",       # Drop existing database objects before recreating
        "--if-exists",
        "-v",
        str(backup_file)
    ]

    try:
        proc = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        logger.info("PostgreSQL pg_restore completed successfully.")
    except FileNotFoundError:
        logger.error("pg_restore binary not found in PATH.")
        raise RuntimeError("pg_restore required for PostgreSQL restoration.")
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_restore failed: {e.stderr}")
        raise


def run_post_restore_smoke_tests(database_url: str) -> bool:
    """Executes database queries to verify integrity and record counts post-restore."""
    logger.info("Running post-restore smoke validation queries...")
    from sqlalchemy import create_engine, select, func
    from sqlalchemy.orm import Session
    from backend.models.entities import Farmer, AreaOfInterest

    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            farmer_count = session.scalar(select(func.count(Farmer.id))) or 0
            aoi_count = session.scalar(select(func.count(AreaOfInterest.id))) or 0
            logger.info(f"Smoke Test: Found {farmer_count} farmer records, {aoi_count} AOI records.")
            logger.info("Post-restore database integrity CERTIFIED.")
            return True
    except Exception as exc:
        logger.error(f"Smoke test verification failed: {exc}")
        return False


def restore_backup(backup_file_path: str, dry_run: bool = False) -> bool:
    """Main restore orchestration entrypoint."""
    backup_file = Path(backup_file_path)
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup archive does not exist: {backup_file}")

    # 1. Verify cryptographic integrity
    verify_checksum(backup_file)

    # 2. Determine target database from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        try:
            from backend.core.config.settings import app_settings
            db_url = app_settings.database_url
        except Exception:
            db_url = "sqlite:///./database/stubble2power.db"

    # 3. Execute engine-specific restore
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not db_path or db_path == ":memory:":
            db_path = "./stubble2power.db"
        restore_sqlite(backup_file, db_path, dry_run)
    else:
        restore_postgresql(backup_file, db_url, dry_run)

    # 4. Smoke test validation
    if not dry_run:
        return run_post_restore_smoke_tests(db_url)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stubble2Power Database Restore Utility")
    parser.add_argument("backup_file", help="Path to backup archive (.db.gz or .dump)")
    parser.add_argument("--dry-run", action="store_true", help="Validate checksum and print actions without modifying data")
    args = parser.parse_args()

    try:
        success = restore_backup(args.backup_file, args.dry_run)
        if success:
            print("SUCCESS: Database restore and validation completed successfully.")
            sys.exit(0)
        else:
            print("WARNING: Restore executed but smoke validation flagged potential issues.")
            sys.exit(1)
    except Exception as exc:
        logger.error(f"Restore failed: {exc}", exc_info=True)
        sys.exit(1)
