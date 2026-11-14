"""
SQLAlchemy ORM Entities for Stubble2Power.
Defines models for Users, Organizations, Farmers, Satellite Observations,
Harmonization Runs, Calendar Aggregates, and Configuration.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, Text, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.models.database import Base


# ============================================================================
# USER AND ORGANIZATIONAL ENTITIES
# ============================================================================

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    org_type: Mapped[str] = mapped_column(String(50), default="AGRICULTURAL_COOP")
    country: Mapped[str] = mapped_column(String(50), default="IND")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[List["User"]] = relationship("User", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="OPERATOR")  # ADMIN, OPERATOR, RESEARCHER
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped[Optional[Organization]] = relationship("Organization", back_populates="users")


# ============================================================================
# AGRICULTURAL ENTITIES
# ============================================================================

class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    village: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(150), default="Punjab", index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(50), default="IND", nullable=False)
    acres: Mapped[float] = mapped_column(Float, nullable=False)
    stubble_tons: Mapped[float] = mapped_column(Float, nullable=False)
    harvest_date: Mapped[date] = mapped_column(Date, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_farmer_coords", "latitude", "longitude"),
        Index("idx_farmer_region", "state", "district", "village"),
    )


class AdministrativeRegion(Base):
    __tablename__ = "administrative_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country_code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)  # IND
    state_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    center_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    center_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    bbox: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # min_lon,min_lat,max_lon,max_lat


class AreaOfInterest(Base):
    __tablename__ = "areas_of_interest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country_code: Mapped[str] = mapped_column(String(10), default="IND")
    min_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    max_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    min_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    max_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ============================================================================
# NASA SATELLITE OBSERVATIONS & INGESTION
# ============================================================================

class SatelliteProduct(Base):
    __tablename__ = "satellite_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # MODIS_NRT, VIIRS_NOAA20_NRT
    satellite_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Terra, Aqua, NOAA-20, Suomi-NPP
    instrument: Mapped[str] = mapped_column(String(50), nullable=False)  # MODIS, VIIRS
    spatial_resolution_meters: Mapped[int] = mapped_column(Integer, nullable=False)  # 1000 or 375
    processing_level: Mapped[str] = mapped_column(String(50), default="NRT")  # NRT or Standard
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    satellite: Mapped[str] = mapped_column(String(50), nullable=False)
    instrument: Mapped[str] = mapped_column(String(50), nullable=False)
    source_endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    date_start: Mapped[date] = mapped_column(Date, nullable=False)
    date_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    records_retrieved: Mapped[int] = mapped_column(Integer, default=0)
    records_valid: Mapped[int] = mapped_column(Integer, default=0)
    records_quarantined: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class RawSatelliteObservation(Base):
    """Immutable raw observation layer preserving untouched source payload."""
    __tablename__ = "raw_satellite_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ingestion_job_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingestion_jobs.id"), index=True)
    record_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    source_satellite: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NormalizedSatelliteObservation(Base):
    """Canonical standardized observation layer with sensor-specific fields preserved."""
    __tablename__ = "normalized_satellite_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_record_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    ingestion_job_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingestion_jobs.id"), index=True)
    satellite: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    instrument: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    product_version: Mapped[str] = mapped_column(String(50), default="6.1NRT")
    acquisition_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    acquisition_time_utc: Mapped[str] = mapped_column(String(10), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    brightness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bright_t31: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_raw: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_normalized: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    daynight: Mapped[str] = mapped_column(String(10), default="D")
    scan: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    track: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spatial_grid_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    quarantine_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_norm_obs_spatial_temporal", "acquisition_date", "latitude", "longitude"),
        Index("idx_norm_obs_grid_date", "spatial_grid_id", "acquisition_date"),
    )


# ============================================================================
# SCIENTIFIC HARMONIZATION ENTITIES
# ============================================================================

class HarmonizationRun(Base):
    __tablename__ = "harmonization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_start: Mapped[date] = mapped_column(Date, nullable=False)
    date_end: Mapped[date] = mapped_column(Date, nullable=False)
    grid_resolution_deg: Mapped[float] = mapped_column(Float, default=0.05)
    total_input_observations: Mapped[int] = mapped_column(Integer, default=0)
    harmonized_cells_count: Mapped[int] = mapped_column(Integer, default=0)
    associated_pairs_count: Mapped[int] = mapped_column(Integer, default=0)
    mean_consensus_score: Mapped[float] = mapped_column(Float, default=0.0)
    algorithm_version: Mapped[str] = mapped_column(String(50), default="1.0.0-scientific")
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED")
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    harmonized_observations: Mapped[List["HarmonizedObservation"]] = relationship(
        "HarmonizedObservation", back_populates="harmonization_run", cascade="all, delete-orphan"
    )


class HarmonizedObservation(Base):
    __tablename__ = "harmonized_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    harmonization_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("harmonization_runs.id"), index=True)
    grid_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lon: Mapped[float] = mapped_column(Float, nullable=False)
    modis_count: Mapped[int] = mapped_column(Integer, default=0)
    viirs_count: Mapped[int] = mapped_column(Integer, default=0)
    total_detections: Mapped[int] = mapped_column(Integer, default=0)
    associated_pairs_count: Mapped[int] = mapped_column(Integer, default=0)
    modis_mean_frp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    viirs_mean_frp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    harmonized_frp_mw: Mapped[float] = mapped_column(Float, default=0.0)
    harmonized_activity_index: Mapped[float] = mapped_column(Float, default=0.0)  # 0 to 100
    consensus_score: Mapped[float] = mapped_column(Float, default=1.0)  # 0 to 1
    uncertainty_level: Mapped[str] = mapped_column(String(20), default="LOW")
    data_coverage_flag: Mapped[str] = mapped_column(String(50), default="DUAL_SENSOR")

    harmonization_run: Mapped[HarmonizationRun] = relationship(
        "HarmonizationRun", back_populates="harmonized_observations"
    )

    __table_args__ = (
        Index("idx_harm_date_grid", "observation_date", "grid_id"),
        Index("idx_harm_coords", "centroid_lat", "centroid_lon"),
    )


# ============================================================================
# CALENDAR AGGREGATES & CONFIG REGISTRY ENTITIES
# ============================================================================

class DailyActivityAggregate(Base):
    __tablename__ = "daily_activity_aggregates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    modis_detections: Mapped[int] = mapped_column(Integer, default=0)
    viirs_detections: Mapped[int] = mapped_column(Integer, default=0)
    total_detections: Mapped[int] = mapped_column(Integer, default=0)
    associated_detections: Mapped[int] = mapped_column(Integer, default=0)
    harmonized_activity_index: Mapped[float] = mapped_column(Float, default=0.0)
    total_frp_mw: Mapped[float] = mapped_column(Float, default=0.0)
    coverage_status: Mapped[str] = mapped_column(String(50), default="COMPLETE")


class ConfigParameter(Base):
    __tablename__ = "config_parameters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url_or_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_date: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
