"""
Configuration Management API Endpoints.
Provides visibility and runtime modification for versioned configuration parameters.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import ConfigurationError

router = APIRouter(prefix="/config", tags=["Configuration Registry"])


@router.get("/")
def list_configuration():
    """Lists all active configuration parameters with scientific provenance and validation bounds."""
    registry = config_manager.get_all()
    return {k: v.model_dump() for k, v in registry.items()}


@router.get("/{param_name}")
def get_configuration_parameter(param_name: str):
    """Retrieves specific parameter metadata and active value."""
    try:
        meta = config_manager.get_metadata(param_name)
        return meta.model_dump()
    except ConfigurationError as e:
        raise HTTPException(status_code=404, detail=str(e))
