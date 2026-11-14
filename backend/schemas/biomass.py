"""
Pydantic Schemas for Agricultural Biomass Estimation, Quality, and Inventory Tracking.
"""

from datetime import date, datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field


class BiomassEstimationRequest(BaseModel):
    farm_crop_id: int
    actual_grain_yield_tons: Optional[float] = None
    moisture_content_pct: Optional[float] = Field(None, ge=5.0, le=40.0)
    retained_fraction_override: Optional[float] = Field(None, ge=0.0, le=0.8)
    competing_demand_fraction_override: Optional[float] = Field(None, ge=0.0, le=0.8)


class BiomassEstimateResponse(BaseModel):
    id: int
    farm_crop_id: int
    harvest_record_id: Optional[int] = None
    gross_residue_tons: float
    retained_residue_tons: float
    competing_demand_tons: float
    collectable_residue_tons: float
    handling_loss_tons: float
    net_usable_biomass_tons: float
    moisture_content_pct: float
    dry_matter_tons: float
    estimation_source: str  # MEASURED, FARMER_REPORTED, OFFICIAL_STATISTICS, SCIENTIFIC_MODEL
    confidence_score: float
    availability_start_date: date
    availability_end_date: date
    methodology_notes: str
    created_at: datetime


class BiomassInventoryTransactionCreate(BaseModel):
    biomass_estimate_id: int
    farm_id: int
    quantity_tons: float = Field(..., gt=0.0)
    stage: str  # ESTIMATED, CONFIRMED, COMMITTED, COLLECTED, STORED, ALLOCATED, PROCESSED
    allocated_unit_id: Optional[int] = None
    notes: Optional[str] = None


class BiomassInventoryTransactionResponse(BaseModel):
    id: int
    biomass_estimate_id: int
    farm_id: int
    quantity_tons: float
    stage: str
    allocated_unit_id: Optional[int] = None
    transaction_timestamp: datetime
    notes: Optional[str] = None


class BiomassAvailabilitySummary(BaseModel):
    total_gross_residue_tons: float
    total_retained_soil_tons: float
    total_competing_fodder_tons: float
    total_collectable_tons: float
    total_net_usable_tons: float
    confirmed_available_tons: float
    committed_to_processing_tons: float
    processed_tons: float
    unallocated_usable_tons: float
    crop_wise_summary: Dict[str, float]
    district_wise_summary: Dict[str, float]
