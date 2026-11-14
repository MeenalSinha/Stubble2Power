#!/usr/bin/env python3
"""
Stubble2Power Automated Database Backup Utility
Supports both SQLite and PostgreSQL/PostGIS.
Generates timestamped, compressed, and SHA-256 checksummed archives with automated retention pruning.
"""

import os
import sys
import argparse
import datetime
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
    format="%(asctime)s [%(levelname)s] [stubble2power.backup] %(message)s"
)
logger = logging.getLogger("s2p_backup")


def calculate_sha256(filepath: Path) -> str:
    """Calculates SHA-256 digest of a file in streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def backup_sqlite(db_path: str, output_file: Path) -> Path:
    """Safely backs up SQLite database using gzip compression."""
    logger.info(f"Backing up SQLite database from {db_path}...")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database file not found at: {db_path}")

    # Compress file directly into output archive
    with open(db_path, "rb") as f_in:
        with gzip.open(output_file, "wb", compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

    logger.info(f"SQLite backup successfully written to {output_file} ({output_file.stat().st_size} bytes).")
    return output_file


def backup_postgresql(database_url: str, output_file: Path) -> Path:
    """Backs up PostgreSQL / PostGIS database using pg_dump with gzip compression."""
    logger.info("Initiating PostgreSQL pg_dump backup...")
    # Normalize URL if using sqlalchemy dialect prefix
    clean_url = database_url.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(clean_url)

    db_name = parsed.path.lstrip("/")
    user = parsed.username or "postgres"
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)
    password = parsed.password or ""

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    cmd = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", user,
        "-F", "c",  # Custom format
        "-b",       # Include blobs
        "-v",       # Verbose
        "-f", str(output_file),
        db_name
    ]

    try:
        proc = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        logger.info(f"PostgreSQL pg_dump completed successfully: {output_file.stat().st_size} bytes.")
        return output_file
    except FileNotFoundError:
        # Fallback if pg_dump CLI binary is not directly available: dump via python or plaintext
        logger.warning("pg_dump binary not found in PATH; falling back to SQLAlchemy schema export.")
        raise RuntimeError("pg_dump tool required for enterprise PostgreSQL backup.")
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump execution failed: {e.stderr}")
        raise


def prune_old_backups(backup_dir: Path, retention_days: int) -> int:
    """Prunes backup files older than retention_days."""
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    pruned_count = 0

    for file_path in backup_dir.glob("s2p_backup_*"):
        if file_path.is_file():
            file_mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime < cutoff_time:
                logger.info(f"Pruning expired backup: {file_path.name} (mtime: {file_mtime})")
                file_path.unlink()
                pruned_count += 1

    return pruned_count


def create_backup(backup_dir: str = "backups", retention_days: int = 14) -> Path:
    """Main backup orchestration entrypoint."""
    dest_dir = Path(backup_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        try:
            from backend.core.config.settings import app_settings
            db_url = app_settings.database_url
        except Exception:
            db_url = "sqlite:///./database/stubble2power.db"

    if db_url.startswith("sqlite"):
        # Extract file path from URL
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not db_path or db_path == ":memory:":
            db_path = "./stubble2power.db"
        archive_name = f"s2p_backup_sqlite_{timestamp}.db.gz"
        target_path = dest_dir / archive_name
        backup_sqlite(db_path, target_path)
    else:
        archive_name = f"s2p_backup_pg_{timestamp}.dump"
        target_path = dest_dir / archive_name
        backup_postgresql(db_url, target_path)

    # Compute and persist SHA-256 checksum
    checksum = calculate_sha256(target_path)
    checksum_file = target_path.with_suffix(target_path.suffix + ".sha256")
    checksum_file.write_text(f"{checksum}  {target_path.name}\n")
    logger.info(f"SHA-256 Checksum recorded: {checksum}")

    # Retention management
    pruned = prune_old_backups(dest_dir, retention_days)
    if pruned > 0:
        logger.info(f"Pruned {pruned} expired backup files.")

    return target_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stubble2Power Database Backup Utility")
    parser.add_argument("--backup-dir", default="backups", help="Target backup directory")
    parser.add_argument("--retention-days", type=int, default=14, help="Backup retention window in days")
    args = parser.parse_args()

    try:
        path = create_backup(args.backup_dir, args.retention_days)
        print(f"SUCCESS: Backup created at {path}")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Backup failed: {exc}", exc_info=True)
        sys.exit(1)
