# Stubble2Power - Engineering Changelog

## [2.0.0] - 2026-11-14

### Completed Across Phases 0–7

#### Phase 0: Forensic Audit & Baseline Testing
- Conducted exhaustive code audit of legacy `app.py` (1,679 lines).
- Identified critical UI defects (premature `return` statements breaking subsequent tabs and footer, dangling Plotly call, Euclidean degree-distance distortions).
- Established baseline regression test suite (`tests/regression/test_legacy_calculations.py`) verifying mathematical parity with legacy scenarios.
- Authored `docs/AUDIT_AND_DEBT_REPORT.md`.

#### Phase 1: Modular Architecture & Separation of Concerns
- Created clean modular directory structure (`backend/`, `frontend/streamlit_app/`, `database/`, `tests/`, `docs/`).
- Extracted business logic into pure Python services (`FarmerService`, `ClusteringService`, `EconomicsService`, `EnvironmentalService`, `GeospatialService`).
- Implemented `backend/core/config/settings.py` eliminating hardcoded values with versioned `ConfigMetadata`.
- Built structured logging with automatic secret masking in `backend/core/logging/logger.py`.
- Introduced FastAPI REST framework (`backend/api/` & `backend/main.py`) with full OpenAPI documentation.

#### Phase 2: Database & Data Management Infrastructure
- Implemented SQLAlchemy ORM relational models in `backend/models/entities.py` supporting PostgreSQL/PostGIS in production and SQLite in testing.
- Created repository layer: `FarmerRepository`, `SatelliteRepository`, `HarmonizationRepository`.
- Built persistent farmer registration, filtering, search, and CSV import/export.
- Provided Alembic migration setup (`alembic.ini`, `database/migrations/`).
- Created automated seed pipeline in `database/seeds/seed_data.py`.

#### Phase 3: NASA FIRMS Integration & Ingestion Engine
- Implemented `NASAClient` in `backend/services/nasa/client.py` for NASA FIRMS REST API (`/api/country/`, `/api/area/`, `/api/data_availability/`).
- Added multi-product support: MODIS (Terra/Aqua) and VIIRS (NOAA-20, Suomi-NPP, NOAA-21).
- Enforced secure MAP_KEY handling via environment variables (`NASA_FIRMS_MAP_KEY` / `FIRMS_MAP_KEY`).
- Implemented `IngestionJob` lifecycle tracking (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
- Created immutable raw observation storage (`raw_satellite_observations`) preserving original payloads.

#### Phase 4: Satellite Data Quality Control & Normalization
- Implemented `QualityControlService` in `backend/services/fire/quality_service.py`.
- Built sensor-aware confidence normalization: MODIS percentage 0-100 -> [0.0, 1.0], VIIRS categorical (`l`, `n`, `h`) -> [0.3, 0.7, 1.0].
- Added timestamp UTC normalization and coordinate bound validation.
- Implemented idempotent SHA-256 observation hashing for deduplication.
- Built quarantine engine capturing invalid records with rejection audit reasons.

#### Phase 5: Scientific MODIS–VIIRS Harmonization Engine
- Created `HarmonizationEngine` in `backend/services/harmonization/engine.py`.
- Implemented discrete global spatial gridding (default 0.05° ≈ 5 km cells).
- Built cross-sensor association service matching candidate pairs within spatial threshold (1.5 km) and temporal window (3.0 hours).
- Formulated Fire Radiative Power (FRP) intercalibration using Wooster et al. (2021) regression ($\beta = 1.04$).
- Derived Normalized Burning Activity Index (0 to 100) and Sensor Consensus Score (0.0 to 1.0).
- Implemented uncertainty classification (`LOW`, `MODERATE`, `HIGH`) and coverage indicators (`DUAL_SENSOR`, `VIIRS_ONLY`, etc.).

#### Phase 6: Historical Burning Activity Calendar
- Implemented `CalendarAggregationService` in `backend/services/calendar/service.py`.
- Developed dynamic daily, weekly, monthly, and annual burning calendars.
- Built coverage status indicators distinguishing real zero burning from lack of satellite overpass.
- Created seasonal burning signature detection (Kharif peak burning window).
- Added CSV and GeoJSON export capability.

#### Phase 7: Advanced Geospatial Intelligence Dashboard
- Upgraded Streamlit frontend in `app.py` with multi-system switcher and glassmorphism UI.
- Integrated multi-layer Folium mapping: MODIS (1km red), VIIRS (375m orange), Harmonized Activity Grid (colored by 0-100 index), Farmer Residue Sources (green), and Mobile Units (truck icons).
- Added interactive popups showing coordinates, satellite, overpass time, FRP, confidence, and consensus.
- Verified and preserved all 5 original sections (Home, Data Input, Clustering, Economics, Executive Dashboard).
- Eliminated all legacy UI `return` bugs and isolated code anomalies.
