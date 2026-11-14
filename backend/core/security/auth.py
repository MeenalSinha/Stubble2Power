"""
JSON Web Token (JWT) Identity & Token Management Service.
Handles cryptographically signed token generation, validation, and session verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import time
import jwt
import hashlib

from backend.core.config.settings import config_manager
from backend.core.exceptions.base import AuthenticationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.security.auth")


def get_jwt_secret_key() -> str:
    return str(config_manager.get("security.jwt_secret_key"))


def get_jwt_algorithm() -> str:
    return str(config_manager.get("security.jwt_algorithm"))


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    organization_id: Optional[int] = None,
    farmer_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a signed HMAC-SHA256 JWT access token."""
    expire_minutes = int(config_manager.get("security.access_token_expire_minutes"))
    now_ts = time.time()
    exp_ts = now_ts + (expires_delta.total_seconds() if expires_delta else expire_minutes * 60)
    
    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role,
        "organization_id": organization_id,
        "farmer_id": farmer_id,
        "type": "access",
        "iat": int(now_ts),
        "exp": int(exp_ts)
    }
    
    secret = get_jwt_secret_key()
    algo = get_jwt_algorithm()
    return jwt.encode(payload, secret, algorithm=algo)


def create_refresh_token(
    user_id: int,
    username: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a long-lived signed JWT refresh token."""
    expire_days = int(config_manager.get("security.refresh_token_expire_days"))
    now_ts = time.time()
    exp_ts = now_ts + (expires_delta.total_seconds() if expires_delta else expire_days * 86400)
    
    payload = {
        "sub": username,
        "user_id": user_id,
        "type": "refresh",
        "iat": int(now_ts),
        "exp": int(exp_ts)
    }
    
    secret = get_jwt_secret_key()
    algo = get_jwt_algorithm()
    return jwt.encode(payload, secret, algorithm=algo)


def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and cryptographically verifies an identity JWT."""
    secret = get_jwt_secret_key()
    algo = get_jwt_algorithm()
    try:
        payload = jwt.decode(token, secret, algorithms=[algo])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(message="Authentication token has expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(message=f"Invalid authentication token: {str(e)}")


def compute_token_hash(token: str) -> str:
    """Computes a SHA-256 hash of a token for safe database session indexing."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
