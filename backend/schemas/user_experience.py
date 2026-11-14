"""
Pydantic Schemas for Phase 13 User Experience: Preferences, Notifications, and Reports.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UserPreferenceUpdate(BaseModel):
    preferred_language: Optional[str] = Field(None, pattern="^(en|hi|pa)$")
    theme: Optional[str] = Field(None, pattern="^(light|dark)$")
    default_aoi: Optional[str] = None
    dashboard_layout: Optional[str] = None
    notification_channels: Optional[Dict[str, Any]] = None


class UserPreferenceResponse(BaseModel):
    id: int
    user_id: int
    preferred_language: str
    theme: str
    default_aoi: str
    dashboard_layout: str
    notification_channels: Dict[str, Any]
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(..., max_length=150)
    message: str
    category: str = Field(default="SYSTEM", description="SYSTEM, HARVEST, COLLECTION, DEPLOYMENT, SECURITY, REPORT")
    priority: str = Field(default="NORMAL", description="LOW, NORMAL, HIGH, CRITICAL")
    action_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    category: str
    read_status: bool
    priority: str
    action_url: Optional[str] = None
    metadata_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class SavedReportCreate(BaseModel):
    report_type: str = Field(..., description="FARMER_DIRECTORY, BIOMASS_INVENTORY, DEPLOYMENT_DISPATCH, FINANCIAL_PROJECTION, LCA_IMPACT, FIRE_INTELLIGENCE")
    title: str = Field(..., max_length=200)
    parameters_json: Optional[Dict[str, Any]] = None
    file_format: str = Field(default="CSV", description="CSV, JSON, SUMMARY")


class SavedReportResponse(BaseModel):
    id: int
    user_id: int
    organization_id: Optional[int] = None
    report_type: str
    title: str
    parameters_json: Dict[str, Any]
    file_format: str
    summary_data_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
