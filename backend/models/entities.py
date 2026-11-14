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
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, default="ORG-MAIN")
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    org_type: Mapped[str] = mapped_column(String(50), default="AGRICULTURAL_COOP")
    country: Mapped[str] = mapped_column(String(50), default="IND")
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    memberships: Mapped[List["OrganizationMembership"]] = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    full_name: Mapped[str] = mapped_column(String(150), default="")
    role: Mapped[str] = mapped_column(String(50), default="OPERATOR")  # Legacy role
    role_name: Mapped[str] = mapped_column(String(50), default="OPERATOR", index=True)
    farmer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("farmers.id"), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization: Mapped[Optional[Organization]] = relationship("Organization", back_populates="users")
    farmer: Mapped[Optional["Farmer"]] = relationship("Farmer", foreign_keys=[farmer_id])
    preferences: Mapped[Optional["UserPreference"]] = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="sessions")


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    org_role: Mapped[str] = mapped_column(String(50), default="MEMBER")  # OWNER, MANAGER, MEMBER, OPERATOR
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped[Organization] = relationship("Organization", back_populates="memberships")
    user: Mapped[User] = relationship("User")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user_membership"),
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # FIRE, FARM, BIOMASS, DEPLOYMENT, FINANCE, LCA, ADMIN, PRIVACY
    description: Mapped[str] = mapped_column(String(255), nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    permission_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("role_name", "permission_name", name="uq_role_permission"),
    )


# ============================================================================
# AGRICULTURAL ENTITIES
# ============================================================================

class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
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
    phone_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    address_line: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farms: Mapped[List["Farm"]] = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")

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
    sensor_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
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


# ============================================================================
# PHASE 8: HISTORICAL BASELINES, SEASONAL PROFILES & ANOMALIES
# ============================================================================

class HistoricalBaseline(Base):
    __tablename__ = "historical_baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    region_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    grid_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    analysis_period: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "OCT_NOV_MULTIYEAR"
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # harmonized_frp_mw, activity_index, detections
    day_of_year: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    mean_val: Mapped[float] = mapped_column(Float, default=0.0)
    median_val: Mapped[float] = mapped_column(Float, default=0.0)
    std_val: Mapped[float] = mapped_column(Float, default=0.0)
    mad_val: Mapped[float] = mapped_column(Float, default=0.0)  # Median Absolute Deviation * 1.4826
    p75_val: Mapped[float] = mapped_column(Float, default=0.0)
    p90_val: Mapped[float] = mapped_column(Float, default=0.0)
    min_val: Mapped[float] = mapped_column(Float, default=0.0)
    max_val: Mapped[float] = mapped_column(Float, default=0.0)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    data_coverage_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    data_sufficiency_status: Mapped[str] = mapped_column(String(50), default="SUFFICIENT")  # SUFFICIENT, LIMITED_HISTORY, INSUFFICIENT_COVERAGE
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_baseline_reg_metric", "region_id", "metric_type", "day_of_year"),
    )


class SeasonalProfile(Base):
    __tablename__ = "seasonal_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    region_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    season_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Kharif_PostHarvest, Rabi_PostHarvest, Annual
    onset_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    peak_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    decay_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_activity: Mapped[float] = mapped_column(Float, default=0.0)
    peak_activity: Mapped[float] = mapped_column(Float, default=0.0)
    duration_days: Mapped[int] = mapped_column(Integer, default=0)
    profile_curve_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("region_id", "year", "season_name", name="uq_seasonal_profile"),
    )


class FireActivityAnomaly(Base):
    __tablename__ = "fire_activity_anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    observation_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    grid_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    region_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    observed_activity: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_metric: Mapped[str] = mapped_column(String(50), default="harmonized_frp_mw")
    baseline_value: Mapped[float] = mapped_column(Float, default=0.0)
    z_score: Mapped[float] = mapped_column(Float, default=0.0)
    mad_score: Mapped[float] = mapped_column(Float, default=0.0)
    ewma_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False)  # SPIKE, PROLONGED_ELEVATION, UNSEASONAL_TIMING, SPATIAL_CLUSTER, EARLY_ONSET, LATE_SURGE
    severity_level: Mapped[str] = mapped_column(String(20), default="MODERATE")  # LOW, MODERATE, HIGH, CRITICAL
    data_sufficiency_flag: Mapped[str] = mapped_column(String(50), default="SUFFICIENT")  # SUFFICIENT, UNCERTAIN_LIMITED_BASELINE
    explanation_json: Mapped[dict] = mapped_column(JSON, default=dict)
    centroid_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    centroid_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_anomaly_date_severity", "observation_date", "severity_level"),
        Index("idx_anomaly_region_type", "region_id", "anomaly_type"),
    )


# ============================================================================
# PHASE 9: AGRICULTURAL REFERENCE & FIRE CONTEXT INTELLIGENCE
# ============================================================================

class CropCalendar(Base):
    __tablename__ = "crop_calendars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    crop_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # Paddy / Rice (Kharif), Wheat (Rabi)
    state_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # Punjab, Haryana, National
    district_name: Mapped[str] = mapped_column(String(100), default="ALL")
    season_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Kharif, Rabi, Zaid
    sowing_start_month_day: Mapped[str] = mapped_column(String(10), nullable=False)  # "06-15"
    sowing_end_month_day: Mapped[str] = mapped_column(String(10), nullable=False)    # "07-15"
    harvest_start_month_day: Mapped[str] = mapped_column(String(10), nullable=False) # "10-01"
    harvest_end_month_day: Mapped[str] = mapped_column(String(10), nullable=False)   # "11-30"
    peak_burn_start_month_day: Mapped[str] = mapped_column(String(10), nullable=False) # "10-15"
    peak_burn_end_month_day: Mapped[str] = mapped_column(String(10), nullable=False)   # "11-20"
    stubble_burning_susceptibility: Mapped[str] = mapped_column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    official_source: Mapped[str] = mapped_column(String(200), nullable=False)
    citation: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_crop_cal_state_crop", "state_name", "crop_name"),
    )


class LandUseRecord(Base):
    __tablename__ = "land_use_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    state_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    land_use_class: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # CROPLAND, FOREST, URBAN_INDUSTRIAL, WETLAND_WATER, BARREN_SCRUB
    min_lat: Mapped[float] = mapped_column(Float, nullable=False)
    min_lon: Mapped[float] = mapped_column(Float, nullable=False)
    max_lat: Mapped[float] = mapped_column(Float, nullable=False)
    max_lon: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(200), default="ESA WorldCover 10m / NRSC Bhuvan")
    confidence: Mapped[float] = mapped_column(Float, default=0.90)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_lulc_spatial", "min_lat", "max_lat", "min_lon", "max_lon"),
    )


class AgriculturalContextAssessment(Base):
    __tablename__ = "agricultural_context_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    harmonized_observation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("harmonized_observations.id"), nullable=True, index=True
    )
    observation_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    grid_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    land_use_class: Mapped[str] = mapped_column(String(50), nullable=False)
    land_use_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    matched_crop: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    harvest_window_status: Mapped[str] = mapped_column(String(50), default="OFF_SEASON")  # IN_PEAK_HARVEST_WINDOW, IN_EXTENDED_HARVEST_WINDOW, OFF_SEASON, UNKNOWN
    context_classification: Mapped[str] = mapped_column(String(60), index=True, nullable=False)  # LIKELY_AGRICULTURAL_CONTEXT, POSSIBLE_AGRICULTURAL_CONTEXT, OTHER_LAND_USE_CONTEXT, UNKNOWN_OR_INSUFFICIENT_EVIDENCE
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0
    distance_to_cropland_km: Mapped[float] = mapped_column(Float, default=0.0)
    stubble_risk_index: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_agri_ctx_date_class", "observation_date", "context_classification"),
    )


# ============================================================================
# PHASE 10: FARM & BIOMASS MANAGEMENT ENTITIES
# ============================================================================

class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id"), index=True, nullable=False)
    farm_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    total_acres: Mapped[float] = mapped_column(Float, nullable=False)
    village: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(150), default="Punjab", index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    boundary_geojson: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ownership_status: Mapped[str] = mapped_column(String(50), default="OWNED")  # OWNED, LEASED, OPERATED
    soil_type: Mapped[str] = mapped_column(String(50), default="ALLUVIAL")
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="farms")
    crops: Mapped[List["FarmCrop"]] = relationship("FarmCrop", back_populates="farm", cascade="all, delete-orphan")


class FarmCrop(Base):
    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), index=True, nullable=False)
    crop_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # PADDY, WHEAT, COTTON, SUGARCANE, MAIZE
    cultivated_acres: Mapped[float] = mapped_column(Float, nullable=False)
    crop_season: Mapped[str] = mapped_column(String(50), nullable=False)  # Kharif, Rabi, Zaid, Perennial
    crop_year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    sowing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_yield_tons_per_acre: Mapped[float] = mapped_column(Float, default=2.60)
    actual_yield_tons_per_acre: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cultivation_status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farm: Mapped[Farm] = relationship("Farm", back_populates="crops")
    harvests: Mapped[List["HarvestRecord"]] = relationship("HarvestRecord", back_populates="crop", cascade="all, delete-orphan")
    biomass_estimates: Mapped[List["BiomassEstimate"]] = relationship("BiomassEstimate", back_populates="crop", cascade="all, delete-orphan")


class HarvestRecord(Base):
    __tablename__ = "harvest_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_crop_id: Mapped[int] = mapped_column(Integer, ForeignKey("farm_crops.id"), index=True, nullable=False)
    harvest_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    actual_grain_yield_tons: Mapped[float] = mapped_column(Float, nullable=False)
    grain_moisture_pct: Mapped[float] = mapped_column(Float, default=14.0)
    harvest_method: Mapped[str] = mapped_column(String(50), default="COMBINE_HARVESTER")
    is_measured: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    crop: Mapped[FarmCrop] = relationship("FarmCrop", back_populates="harvests")


class BiomassEstimate(Base):
    __tablename__ = "biomass_estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_crop_id: Mapped[int] = mapped_column(Integer, ForeignKey("farm_crops.id"), index=True, nullable=False)
    harvest_record_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("harvest_records.id"), nullable=True)
    gross_residue_tons: Mapped[float] = mapped_column(Float, nullable=False)
    retained_residue_tons: Mapped[float] = mapped_column(Float, default=0.0)
    competing_demand_tons: Mapped[float] = mapped_column(Float, default=0.0)
    collectable_residue_tons: Mapped[float] = mapped_column(Float, nullable=False)
    handling_loss_tons: Mapped[float] = mapped_column(Float, default=0.0)
    net_usable_biomass_tons: Mapped[float] = mapped_column(Float, nullable=False)
    moisture_content_pct: Mapped[float] = mapped_column(Float, default=14.0)
    dry_matter_tons: Mapped[float] = mapped_column(Float, nullable=False)
    estimation_source: Mapped[str] = mapped_column(String(50), default="SCIENTIFIC_MODEL")  # MEASURED, FARMER_REPORTED, OFFICIAL_STATISTICS, SCIENTIFIC_MODEL
    confidence_score: Mapped[float] = mapped_column(Float, default=0.90)
    availability_start_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    availability_end_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    methodology_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    crop: Mapped[FarmCrop] = relationship("FarmCrop", back_populates="biomass_estimates")
    transactions: Mapped[List["BiomassInventoryTransaction"]] = relationship(
        "BiomassInventoryTransaction", back_populates="biomass_estimate", cascade="all, delete-orphan"
    )


class BiomassInventoryTransaction(Base):
    __tablename__ = "biomass_inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    biomass_estimate_id: Mapped[int] = mapped_column(Integer, ForeignKey("biomass_estimates.id"), index=True, nullable=False)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), index=True, nullable=False)
    quantity_tons: Mapped[float] = mapped_column(Float, nullable=False)
    stage: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # ESTIMATED, CONFIRMED, COMMITTED, COLLECTED, STORED, ALLOCATED, PROCESSED
    allocated_unit_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    transaction_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    biomass_estimate: Mapped[BiomassEstimate] = relationship("BiomassEstimate", back_populates="transactions")


# ============================================================================
# PHASE 11: MOBILE BIO-REFINERY & ROUTE OPTIMIZATION ENTITIES
# ============================================================================

class MobileBioRefinery(Base):
    __tablename__ = "mobile_bio_refineries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    unit_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(50), default="TRAILER_MOUNTED_DENSIFIER")
    technology: Mapped[str] = mapped_column(String(50), default="BRIQUETTING")  # BRIQUETTING, SLOW_PYROLYSIS
    hourly_capacity_tons: Mapped[float] = mapped_column(Float, default=2.5)
    daily_operating_hours: Mapped[float] = mapped_column(Float, default=10.0)
    daily_capacity_tons: Mapped[float] = mapped_column(Float, default=25.0)
    fuel_consumption_liters_per_ton: Mapped[float] = mapped_column(Float, default=4.5)
    operating_cost_per_hour_inr: Mapped[float] = mapped_column(Float, default=750.0)
    current_status: Mapped[str] = mapped_column(String(50), default="AVAILABLE")  # AVAILABLE, DEPLOYED, MAINTENANCE, STANDBY
    home_depot_name: Mapped[str] = mapped_column(String(150), default="Ludhiana Central Depot")
    home_latitude: Mapped[float] = mapped_column(Float, default=30.9010)
    home_longitude: Mapped[float] = mapped_column(Float, default=75.8573)
    max_travel_radius_km: Mapped[float] = mapped_column(Float, default=60.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DeploymentPlan(Base):
    __tablename__ = "deployment_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    plan_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    region: Mapped[str] = mapped_column(String(100), default="Punjab")
    date_start: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    date_end: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPTIMIZED")  # DRAFT, OPTIMIZED, APPROVED, EXECUTED, REJECTED
    total_biomass_assigned_tons: Mapped[float] = mapped_column(Float, default=0.0)
    total_units_deployed: Mapped[int] = mapped_column(Integer, default=0)
    total_route_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_transport_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    unserved_farms_count: Mapped[int] = mapped_column(Integer, default=0)
    capacity_utilization_pct: Mapped[float] = mapped_column(Float, default=0.0)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assignments: Mapped[List["DeploymentAssignment"]] = relationship("DeploymentAssignment", back_populates="deployment_plan", cascade="all, delete-orphan")
    routes: Mapped[List["RoutePlan"]] = relationship("RoutePlan", back_populates="deployment_plan", cascade="all, delete-orphan")


class DeploymentAssignment(Base):
    __tablename__ = "deployment_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deployment_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("deployment_plans.id"), index=True, nullable=False)
    mobile_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("mobile_bio_refineries.id"), index=True, nullable=False)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), index=True, nullable=False)
    assigned_biomass_tons: Mapped[float] = mapped_column(Float, nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    collection_status: Mapped[str] = mapped_column(String(50), default="SCHEDULED")  # SCHEDULED, PICKED_UP, PROCESSED, CANCELLED

    deployment_plan: Mapped[DeploymentPlan] = relationship("DeploymentPlan", back_populates="assignments")
    mobile_unit: Mapped[MobileBioRefinery] = relationship("MobileBioRefinery")
    farm: Mapped[Farm] = relationship("Farm")


class RoutePlan(Base):
    __tablename__ = "route_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deployment_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("deployment_plans.id"), index=True, nullable=False)
    mobile_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("mobile_bio_refineries.id"), index=True, nullable=False)
    route_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    road_tortuosity_ratio: Mapped[float] = mapped_column(Float, default=1.35)
    estimated_duration_hours: Mapped[float] = mapped_column(Float, default=0.0)
    fuel_consumed_liters: Mapped[float] = mapped_column(Float, default=0.0)
    total_payload_tons: Mapped[float] = mapped_column(Float, default=0.0)
    stops_json: Mapped[dict] = mapped_column(JSON, default=dict)
    route_geometry_geojson: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deployment_plan: Mapped[DeploymentPlan] = relationship("DeploymentPlan", back_populates="routes")
    mobile_unit: Mapped[MobileBioRefinery] = relationship("MobileBioRefinery")


# ============================================================================
# PHASE 12: ADVANCED ECONOMICS & LCA ENVIRONMENTAL ENTITIES
# ============================================================================

class FinancialScenario(Base):
    __tablename__ = "financial_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    deployment_plan_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("deployment_plans.id"), nullable=True, index=True)
    scenario_name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # Conservative, Base Case, Optimistic, Custom
    briquette_price_per_ton: Mapped[float] = mapped_column(Float, default=5000.0)
    biochar_price_per_ton: Mapped[float] = mapped_column(Float, default=12000.0)
    farmer_procurement_price_per_ton: Mapped[float] = mapped_column(Float, default=1500.0)
    diesel_price_per_liter: Mapped[float] = mapped_column(Float, default=89.50)
    processing_capex_per_unit: Mapped[float] = mapped_column(Float, default=2500000.0)
    wacc_discount_rate_pct: Mapped[float] = mapped_column(Float, default=10.5)
    total_biomass_processed_tons: Mapped[float] = mapped_column(Float, default=0.0)
    total_revenue_inr: Mapped[float] = mapped_column(Float, default=0.0)
    total_opex_inr: Mapped[float] = mapped_column(Float, default=0.0)
    total_farmer_payments_inr: Mapped[float] = mapped_column(Float, default=0.0)
    total_transport_costs_inr: Mapped[float] = mapped_column(Float, default=0.0)
    total_processing_costs_inr: Mapped[float] = mapped_column(Float, default=0.0)
    gross_profit_inr: Mapped[float] = mapped_column(Float, default=0.0)
    net_margin_pct: Mapped[float] = mapped_column(Float, default=0.0)
    cost_per_ton_processed_inr: Mapped[float] = mapped_column(Float, default=0.0)
    break_even_tons: Mapped[float] = mapped_column(Float, default=0.0)
    roi_pct: Mapped[float] = mapped_column(Float, default=0.0)
    payback_period_years: Mapped[float] = mapped_column(Float, default=0.0)
    npv_inr: Mapped[float] = mapped_column(Float, default=0.0)
    irr_pct: Mapped[float] = mapped_column(Float, default=0.0)
    assumptions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EnvironmentalAssessment(Base):
    __tablename__ = "environmental_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    deployment_plan_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("deployment_plans.id"), nullable=True, index=True)
    biomass_diverted_tons: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_burning_co2_tons: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_burning_ch4_tons: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_burning_n2o_tons: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_burning_pm25_tons: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_total_co2e_tons: Mapped[float] = mapped_column(Float, default=0.0)
    project_transport_emissions_co2_tons: Mapped[float] = mapped_column(Float, default=0.0)
    project_processing_emissions_co2_tons: Mapped[float] = mapped_column(Float, default=0.0)
    project_total_emissions_co2e_tons: Mapped[float] = mapped_column(Float, default=0.0)
    coal_displaced_tons: Mapped[float] = mapped_column(Float, default=0.0)
    avoided_coal_co2e_tons: Mapped[float] = mapped_column(Float, default=0.0)
    biochar_stable_carbon_stored_co2e_tons: Mapped[float] = mapped_column(Float, default=0.0)
    net_avoided_co2e_tons: Mapped[float] = mapped_column(Float, default=0.0)
    net_benefit_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    carbon_credit_eligible_tons: Mapped[float] = mapped_column(Float, default=0.0)
    methodology_provenance: Mapped[str] = mapped_column(String(255), default="IPCC 2006 / AR6 WG1 / CEA CO2 Baseline v19.0")
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ============================================================================
# PHASE 13 & 14: USER EXPERIENCE, GOVERNANCE, PRIVACY & SECURITY ENTITIES
# ============================================================================

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")  # en, hi, pa
    theme: Mapped[str] = mapped_column(String(20), default="light")  # light, dark
    default_aoi: Mapped[str] = mapped_column(String(100), default="Punjab Central")
    dashboard_layout: Mapped[str] = mapped_column(String(50), default="STANDARD")
    notification_channels: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="preferences")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, default="SYSTEM")  # SYSTEM, HARVEST, COLLECTION, DEPLOYMENT, SECURITY, REPORT
    read_status: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL")  # LOW, NORMAL, HIGH, CRITICAL
    action_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped[User] = relationship("User", back_populates="notifications")


class SavedReport(Base):
    __tablename__ = "saved_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    report_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # FARMER_DIRECTORY, BIOMASS_INVENTORY, DEPLOYMENT_DISPATCH, FINANCIAL_PROJECTION, LCA_IMPACT, FIRE_INTELLIGENCE
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    file_format: Mapped[str] = mapped_column(String(20), default="CSV")  # CSV, JSON, SUMMARY
    summary_data_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User")


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id"), index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    consent_purpose: Mapped[str] = mapped_column(String(60), index=True, nullable=False)  # BIOMASS_AGGREGATION, SATELLITE_FIRE_CORRELATION, LOGISTICS_DISPATCH, DIRECT_PAYMENT
    consent_version: Mapped[str] = mapped_column(String(20), default="v1.0")
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    consent_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    farmer: Mapped[Farmer] = relationship("Farmer")


class DataSubjectRequest(Base):
    __tablename__ = "data_subject_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    request_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # ACCESS, CORRECTION, ERASURE, EXPORT
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", index=True)  # SUBMITTED, IN_REVIEW, COMPLETED, REJECTED
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])


class DataRetentionPolicy(Base):
    __tablename__ = "data_retention_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    data_category: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)  # AUDIT_LOGS, USER_SESSIONS, INACTIVE_USERS, FARM_COORDINATES
    retention_period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    legal_basis: Mapped[str] = mapped_column(String(150), nullable=False)
    action_on_expiry: Mapped[str] = mapped_column(String(50), default="DELETE")  # DELETE, ANONYMIZE, ARCHIVE
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_username: Mapped[str] = mapped_column(String(100), default="anonymous", index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # AUTH_LOGIN, DATA_EXPORT, DELETE_RECORD, etc.
    resource_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)  # LOGIN_FAILURE, UNAUTHORIZED_ACCESS, RATE_LIMIT_EXCEEDED, SUSPICIOUS_EXPORT
    severity: Mapped[str] = mapped_column(String(20), index=True, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
