"""
Pydantic Schemas for Farm, Land, and Cultivation Management.
"""

from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class FarmBase(BaseModel):
    farmer_id: int
    farm_name: str
    total_acres: float = Field(..., gt=0.0)
    village: str
    district: str
    state: str = "Punjab"
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    ownership_status: str = "OWNED"  # OWNED, LEASED, OPERATED
    soil_type: str = "ALLUVIAL"
    boundary_geojson: Optional[Dict[str, Any]] = None


class FarmCreate(FarmBase):
    pass


class FarmResponse(FarmBase):
    id: int
    verification_status: str
    created_at: datetime


class FarmCropBase(BaseModel):
    farm_id: Optional[int] = None
    crop_type: str  # PADDY, WHEAT, COTTON, SUGARCANE, MAIZE
    cultivated_acres: float = Field(..., gt=0.0)
    crop_season: str  # Kharif, Rabi, Zaid, Perennial
    crop_year: int
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    expected_yield_tons_per_acre: float = 2.60


class FarmCropCreate(FarmCropBase):
    pass


class FarmCropResponse(FarmCropBase):
    id: int
    farm_id: int
    actual_harvest_date: Optional[date] = None
    actual_yield_tons_per_acre: Optional[float] = None
    cultivation_status: str
    created_at: datetime


class HarvestRecordCreate(BaseModel):
    farm_crop_id: Optional[int] = None
    harvest_date: date
    actual_grain_yield_tons: float = Field(..., ge=0.0)
    grain_moisture_pct: float = Field(14.0, ge=5.0, le=40.0)
    harvest_method: str = "COMBINE_HARVESTER"
    is_measured: bool = True
    notes: Optional[str] = None


class HarvestRecordResponse(BaseModel):
    id: int
    farm_crop_id: int
    harvest_date: date
    actual_grain_yield_tons: float
    grain_moisture_pct: float
    harvest_method: str
    is_measured: bool
    notes: Optional[str] = None
    created_at: datetime
