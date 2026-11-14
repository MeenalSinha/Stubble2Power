"""
Domain exception hierarchy for Stubble2Power.
Provides structured error reporting without exposing sensitive data.
"""

from typing import Optional, Dict, Any


class Stubble2PowerException(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ConfigurationError(Stubble2PowerException):
    """Raised when configuration is missing, invalid, or unverified."""
    def __init__(self, message: str, parameter: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        merged_details = details or {}
        if parameter:
            merged_details["parameter"] = parameter
        super().__init__(message=message, code="CONFIG_ERROR", details=merged_details)


class ValidationError(Stubble2PowerException):
    """Raised when data fails schema or domain validation."""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        merged_details = details or {}
        if field:
            merged_details["field"] = field
        super().__init__(message=message, code="VALIDATION_ERROR", details=merged_details)


class DataNotFoundError(Stubble2PowerException):
    """Raised when an entity or resource is not found."""
    def __init__(self, entity: str = "Resource", identifier: Any = None, message: Optional[str] = None):
        msg = message or f"{entity} with identifier '{identifier}' was not found."
        super().__init__(
            message=msg,
            code="NOT_FOUND",
            details={"entity": entity, "identifier": str(identifier) if identifier is not None else ""}
        )


class NotFoundError(DataNotFoundError):
    """Alias for DataNotFoundError."""
    pass


class NASAAPIError(Stubble2PowerException):
    """Raised when communication with NASA FIRMS API fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, endpoint: Optional[str] = None):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if endpoint:
            # Mask any query parameters that could contain keys
            sanitized = endpoint.split("?")[0] if "?" in endpoint else endpoint
            details["endpoint"] = sanitized
        super().__init__(message=message, code="NASA_API_ERROR", details=details)


class HarmonizationError(Stubble2PowerException):
    """Raised when scientific harmonization fails or encounters invalid data states."""
    def __init__(self, message: str, run_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        merged = details or {}
        if run_id:
            merged["run_id"] = run_id
        super().__init__(message=message, code="HARMONIZATION_ERROR", details=merged)


class DatabaseError(Stubble2PowerException):
    """Raised on relational or spatial database operation failures."""
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {"operation": operation} if operation else {}
        super().__init__(message=message, code="DATABASE_ERROR", details=details)


class AuthenticationError(Stubble2PowerException):
    """Raised when authentication credentials are missing, invalid, or expired."""
    def __init__(self, message: str = "Authentication failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="AUTHENTICATION_FAILED", details=details)


class AuthorizationError(Stubble2PowerException):
    """Raised when an authenticated principal lacks required permission or violates tenant boundary."""
    def __init__(self, message: str = "Permission denied.", role: Optional[str] = None, required_permission: Optional[str] = None):
        details = {}
        if role:
            details["role"] = role
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message=message, code="PERMISSION_DENIED", details=details)


class ConflictError(Stubble2PowerException):
    """Raised when a resource state conflicts with the requested action (e.g. duplicate key)."""
    def __init__(self, message: str, entity: str = "Resource", identifier: Any = None):
        super().__init__(message=message, code="CONFLICT", details={"entity": entity, "identifier": str(identifier) if identifier else ""})
