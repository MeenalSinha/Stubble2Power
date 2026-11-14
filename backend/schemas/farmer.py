"""
Pydantic schemas for Farmer and Farm entity management.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FarmerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Full name of farmer")
    village: str = Field(..., min_length=2, max_length=150, description="Village name")
    district: str = Field(default="Punjab", min_length=2, max_length=150, description="District name")
    state: str = Field(default="Punjab", min_length=2, max_length=150, description="State or province name")
    country: str = Field(default="IND", min_length=2, max_length=50, description="Country code (ISO 3166-1 alpha-3)")
    acres: float = Field(..., gt=0, le=10000, description="Cultivated land area in acres")
    stubble_tons: float = Field(..., gt=0, le=50000, description="Estimated stubble biomass available in metric tons")
    harvest_date: date = Field(default_factory=date.today, description="Harvest completion date")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude coordinate")

    @field_validator('name')
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Farmer name cannot be blank.")
        return cleaned


class FarmerCreate(FarmerBase):
    pass


class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    acres: Optional[float] = None
    stubble_tons: Optional[float] = None
    harvest_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FarmerResponse(FarmerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
