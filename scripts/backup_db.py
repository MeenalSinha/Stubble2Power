#!/usr/bin/env python3
"""
Stubble2Power Automated Database Backup Utility.
Supports SQLite (development/testing) and PostgreSQL/PostGIS (production/staging).
Generates timestamped, compressed, AES-128-CBC/HMAC-SHA256 (Fernet) encrypted,
and cryptographically authenticated backup archives with automated retention pruning.
"""

import os
import sys
import json
import argparse
import datetime
import gzip
import hashlib
import shutil
import subprocess
import logging
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [stubble2power.backup] %(message)s")
logger = logging.getLogger("s2p_backup")


def get_encryption_key(explicit_key: Optional[str] = None) -> bytes:
    """
    Resolves the cryptographic backup encryption key.
    Enforces fail-closed security in production when key is missing.
    """
    key_str = explicit_key or os.getenv("BACKUP_ENCRYPTION_KEY")
    env = os.getenv("APP_ENV", "development").strip().lower()

    if key_str:
        return key_str.strip().encode("utf-8")

    if env in ("production", "prod"):
        raise ValueError(
            "CRITICAL SECURITY FAILURE: BACKUP_ENCRYPTION_KEY environment variable is mandatory "
            "for production backups. Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    # In development/test environments, auto-load or generate local dev key
    dev_key_file = Path("backups/.dev_backup_key")
    if dev_key_file.exists():
        return dev_key_file.read_bytes().strip()

    generated_key = Fernet.generate_key()
    dev_key_file.parent.mkdir(parents=True, exist_ok=True)
    dev_key_file.write_bytes(generated_key)
    logger.warning(
        f"Development mode: generated temporary backup encryption key saved to {dev_key_file}. "
        "In production, BACKUP_ENCRYPTION_KEY must be supplied via secrets manager."
    )
    return generated_key


def calculate_sha256(filepath: Path) -> str:
    """Calculates SHA-256 digest of a file in streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def encrypt_file(input_path: Path, output_path: Path, key: bytes) -> None:
    """
    Encrypts a file using Fernet (AES-128-CBC with PKCS7 padding and HMAC-SHA256 authentication).
    Removes the unencrypted input file upon successful encryption.
    """
    fernet = Fernet(key)
    logger.info(f"Encrypting backup archive {input_path.name} -> {output_path.name}...")

    plaintext_data = input_path.read_bytes()
    encrypted_data = fernet.encrypt(plaintext_data)
    output_path.write_bytes(encrypted_data)

    # Secure cleanup of intermediate unencrypted dump
    input_path.unlink()
    logger.info(f"Encryption complete. Encrypted archive size: {output_path.stat().st_size} bytes.")


def backup_sqlite(db_path: str, output_file: Path) -> Path:
    """Safely dumps and compresses SQLite database using gzip."""
    logger.info(f"Dumping SQLite database from {db_path}...")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database file not found at: {db_path}")

    with open(db_path, "rb") as f_in:
        with gzip.open(output_file, "wb", compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

    logger.info(f"SQLite dump written to temporary archive {output_file} ({output_file.stat().st_size} bytes).")
    return output_file


def backup_postgresql(database_url: str, output_file: Path) -> Path:
    """Backs up PostgreSQL / PostGIS database using pg_dump with custom format."""
    logger.info("Initiating PostgreSQL pg_dump backup...")
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
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-F",
        "c",  # Custom format (compressed)
        "-b",  # Include blobs
        "-v",  # Verbose
        "-f",
        str(output_file),
        db_name,
    ]

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        logger.info(f"PostgreSQL pg_dump completed: {output_file.stat().st_size} bytes.")
        return output_file
    except FileNotFoundError:
        logger.error("pg_dump binary not found in PATH.")
        raise RuntimeError("pg_dump binary is required for PostgreSQL database backups.")
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump execution failed: {e.stderr}")
        raise


def prune_old_backups(backup_dir: Path, retention_days: int) -> int:
    """Prunes backup archives and companion files older than retention_days."""
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    pruned_count = 0

    for file_path in backup_dir.glob("s2p_backup_*"):
        if file_path.is_file():
            file_mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime < cutoff_time:
                logger.info(f"Pruning expired backup artifact: {file_path.name} (mtime: {file_mtime})")
                file_path.unlink()
                pruned_count += 1

    return pruned_count


def create_backup(
    backup_dir: str = "backups",
    retention_days: int = 14,
    encryption_key: Optional[str] = None,
    source_database_url: Optional[str] = None,
) -> Path:
    """
    Main backup orchestration entrypoint.
    1. Extracts database from environment (PostgreSQL in production, SQLite in dev).
    2. Dumps & compresses the database.
    3. Encrypts with AES-128-CBC/HMAC-SHA256 (Fernet).
    4. Computes SHA-256 of encrypted archive.
    5. Writes cryptographic metadata manifest.
    6. Prunes expired archives.
    """
    dest_dir = Path(backup_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    key = get_encryption_key(encryption_key)
    key_fingerprint = hashlib.sha256(key).hexdigest()[:16]

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    db_url = source_database_url or os.getenv("DATABASE_URL")
    if not db_url:
        try:
            from backend.core.config.settings import app_settings

            db_url = app_settings.database_url
        except Exception:
            db_url = "sqlite:///./database/stubble2power.db"

    # Stage 1: Create compressed dump
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not db_path or db_path == ":memory:":
            db_path = "./stubble2power.db"
        raw_dump_name = f"s2p_backup_sqlite_{timestamp}.db.gz.tmp"
        raw_dump_path = dest_dir / raw_dump_name
        backup_sqlite(db_path, raw_dump_path)
        engine_type = "sqlite"
    else:
        raw_dump_name = f"s2p_backup_pg_{timestamp}.dump.tmp"
        raw_dump_path = dest_dir / raw_dump_name
        backup_postgresql(db_url, raw_dump_path)
        engine_type = "postgresql"

    raw_size = raw_dump_path.stat().st_size

    # Stage 2: Encrypt dump
    final_archive_name = f"s2p_backup_{engine_type}_{timestamp}.enc"
    encrypted_path = dest_dir / final_archive_name
    encrypt_file(raw_dump_path, encrypted_path, key)

    # Stage 3: Cryptographic SHA-256 digest of ENCRYPTED payload
    checksum = calculate_sha256(encrypted_path)
    checksum_file = encrypted_path.with_suffix(".enc.sha256")
    checksum_file.write_text(f"{checksum}  {encrypted_path.name}\n")
    logger.info(f"Encrypted archive SHA-256 recorded: {checksum}")

    # Stage 4: Metadata Manifest
    manifest = {
        "archive_file": encrypted_path.name,
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "database_engine": engine_type,
        "encryption_algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)",
        "key_fingerprint_sha256": key_fingerprint,
        "encrypted_sha256": checksum,
        "unencrypted_size_bytes": raw_size,
        "encrypted_size_bytes": encrypted_path.stat().st_size,
        "format_version": "2.0.0-encrypted",
    }
    manifest_file = encrypted_path.with_suffix(".enc.meta.json")
    manifest_file.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Cryptographic manifest written to {manifest_file.name}.")

    # Stage 5: Retention management
    pruned = prune_old_backups(dest_dir, retention_days)
    if pruned > 0:
        logger.info(f"Pruned {pruned} expired backup files.")

    return encrypted_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stubble2Power Secure Database Backup Utility")
    parser.add_argument("--backup-dir", default="backups", help="Target backup directory")
    parser.add_argument("--retention-days", type=int, default=14, help="Backup retention window in days")
    parser.add_argument(
        "--key", default=None, help="Explicit encryption key (defaults to BACKUP_ENCRYPTION_KEY env var)"
    )
    args = parser.parse_args()

    try:
        path = create_backup(args.backup_dir, args.retention_days, args.key)
        print(f"SUCCESS: Encrypted backup created at {path}")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Backup failed: {exc}", exc_info=True)
        sys.exit(1)
