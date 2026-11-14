"""
Health and System Status API Endpoints.
"""

from fastapi import APIRouter
from backend.models.database import check_db_health
from backend.services.nasa.client import NASAClient
from backend.core.config.settings import app_settings

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("/")
@router.get("")
def get_health_status():
    """Returns database, NASA client, and operational status."""
    db_ok = check_db_health()
    nasa_client = NASAClient()
    nasa_configured = nasa_client.is_configured()

    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": app_settings.app_name,
        "environment": app_settings.app_env,
        "database_connected": db_ok,
        "nasa_firms_configured": nasa_configured,
        "api_version": "2.5.0",
    }
