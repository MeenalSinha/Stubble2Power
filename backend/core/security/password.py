"""
Cryptographic Password Hashing & Verification Utilities.
Uses PBKDF2-SHA256 with dynamic per-password cryptographic salts adhering to NIST SP 800-63B standards.
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes a plaintext password using salted PBKDF2-SHA256."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext candidate against stored PBKDF2-SHA256 hash."""
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)
