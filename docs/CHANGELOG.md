# Stubble2Power - Engineering Changelog

## [2.2.0] - 2026-11-14

### Phase 8 & Phase 9 Implementation: Advanced Fire Intelligence & Agricultural Context

#### Phase 8: Seasonal Intelligence & Anomaly Detection
- **Multi-Year Historical Baselines**: Implemented `HistoricalBaselineService` computing multi-year parametric normals ($\mu, \sigma$) and robust non-parametric metrics ($\text{Median}, \text{MAD}, \text{P75}, \text{P90}$) with standard 365-day leap-year alignment.
- **Empirical Seasonal Profiles**: Implemented `SeasonalProfileService` deriving season onset dates (10% cumulative activity), peak dates, decay dates (90% cumulative), duration, and empirical fire activity distribution curves.
- **Data Sufficiency Engine**: Protocol enforcing minimum observation history ($N \ge 3$ periods) and satellite overpass coverage ($\ge 60\%$) before certifying baseline confidence.
- **Multi-Method Statistical Anomaly Detector**: Implemented `StatisticalAnomalyDetector` combining parametric Z-score ($Z \ge 2.5$), robust Median Absolute Deviation ($\text{MAD} \ge 3.0$), EWMA momentum tracking ($\alpha = 0.3$), and spatial clustering ($r = 25\text{ km}$).
- **Diagnostic Explainability**: Implemented `AnomalyExplanationService` generating evidence-based structured JSON diagnostics explaining exact observed values, expected normals, percentage surges, and observational confidence.
- **Database Entities & Persistence**: Added `HistoricalBaseline`, `SeasonalProfile`, and `FireActivityAnomaly` ORM models.
- **REST API Endpoints**: Mounted `/api/seasonal/profiles`, `/api/seasonal/profiles/generate`, `/api/seasonal/baselines`, `/api/seasonal/baselines/compute`, `/api/anomalies`, `/api/anomalies/detect`, and `/api/anomalies/{anomaly_id}`.
- **Interactive UI Dashboard**: Built dedicated Streamlit module `📈 Seasonal & Anomaly Intelligence` with profile curve visualizers, historical normals tables, severity pie breakdowns, and diagnostic evidence inspection.

#### Phase 9: Agricultural Fire Context Intelligence
- **Architectural Boundary Enforcement**: Strictly isolated context classification from Phase 8 statistical anomalies (unusual fire $\ne$ agricultural fire).
- **Authoritative Crop Calendars**: Seeded official Punjab Agricultural University (PAU) and ICAR crop calendars (Kharif Paddy, Rabi Wheat, Kharif Cotton, Sugarcane) with sowing, harvest, and peak residue burn schedules.
- **Land Use Land Cover (LULC) Integration**: Implemented `LandUseService` georeferencing ESA WorldCover and NRSC Bhuvan zones (Central Agri Basin, Western Agri Basin, Majha Basin, Shivalik Forest Reserve, Harike Wetland, Ludhiana Focal Point Industrial Zone).
- **Bayesian Context Classification**: Implemented `AgriculturalClassificationService` classifying observations into `LIKELY_AGRICULTURAL_CONTEXT`, `POSSIBLE_AGRICULTURAL_CONTEXT`, `OTHER_LAND_USE_CONTEXT`, and `UNKNOWN_OR_INSUFFICIENT_EVIDENCE`.
- **Physical Thermal Envelope Verification**: Enforced empirical combustion physics constraint ($\text{FRP} \le 250\text{ MW}$) to differentiate crop field stubble burning from intensive forest crown fires or industrial flares.
- **Database Entities & Persistence**: Added `CropCalendar`, `LandUseRecord`, and `AgriculturalContextAssessment` ORM models.
- **REST API Endpoints**: Mounted `/api/agriculture/calendars`, `/api/agriculture/assessments`, `/api/agriculture/classify`, and `/api/agriculture/summary`.
- **Interactive UI Dashboard**: Built dedicated Streamlit module `🌱 Agricultural Fire Context Intelligence` with Folium classification map, crop calendar directory, live harvest window tester, and attribution evidence explorer.

#### Test Suite & Verification
- Expanded automated test suite to 57 passing tests (100% pass rate).
- Full Docker Compose stack verified with PostGIS, FastAPI backend, and Streamlit frontend.

### Comprehensive Quality Assurance & Scientific Audit Fixes

#### Scientific Calibration & Domain Config Architecture
- **NBAI Formula Parameterization**: Replaced all hardcoded coefficients ($2.5, 3.5, 50.0, 7.0, 35.0, 15.0$) in `HarmonizationEngine._compute_activity_index` with validated parameters in `backend/core/config/settings.py` (`nasa.harmonization.modis_detection_weight`, `nasa.harmonization.detection_index_slope`, `nasa.harmonization.detection_index_cap`, `nasa.harmonization.frp_index_slope`, `nasa.harmonization.frp_index_cap`, `nasa.harmonization.consensus_index_weight`).
- **Uncertainty Classification**: Bound consensus score thresholds ($0.85$ and $0.60$) to versioned configuration entries (`nasa.harmonization.consensus_threshold_high`, `nasa.harmonization.consensus_threshold_low`).
- **Geospatial Centroid Fallbacks**: Added `geospatial.default_map_center_lat` ($30.7333$), `geospatial.default_map_center_lon` ($76.7794$), and `geospatial.default_map_zoom` ($8$) to `ConfigManager` to eliminate hardcoded coordinates in map initialization.
- **Physical Brightness Bounds**: Extracted satellite thermal IR bounds ($150\text{ K} - 600\text{ K}$) into `fire.qc.min_brightness_kelvin` and `fire.qc.max_brightness_kelvin`.

#### Database & Persistence Fixes
- **Harmonization Run Sensor Breakdown**: Added `sensor_breakdown: Mapped[dict] = mapped_column(JSON)` to the `HarmonizationRun` entity and repository, enabling permanent multi-session storage of sensor observation counts.
- **Alembic Migration Integrity**: Upgraded `database/migrations/versions/001_initial_schema.py` from empty pass stubs to explicit `Base.metadata.create_all` and `drop_all` bindings, enabling automated CLI migrations via `alembic upgrade head`.

#### Quality Control & Remote Sensing Enhancements
- **MODIS String Confidence**: Added explicit mapping in `QualityControlService.normalize_confidence` for categorical MODIS confidence strings (`high` $\to 1.0$, `nominal` $\to 0.7$, `low` $\to 0.3$), preventing inaccurate fallback to $0.5$.
- **Zero FRP Normalization**: Validated non-rejection of genuine zero-FRP detections.
- **Spatial Bounding-Box Coverage**: Fixed `CalendarAggregationService.get_daily_calendar` to filter normalized observation counts by bounding box before assigning `ZERO_BURNING` vs `NO_OVERPASS`.

#### Activity Calendar & API Endpoints
- **Weekly Activity Calendar**: Implemented `get_weekly_summaries(year, bbox)` in `CalendarAggregationService` and registered `GET /api/calendar/weekly` endpoint, aggregating ISO-8601 weeks with total detections, peak dates, and mean activity.
- **API Test Suite**: Added `tests/integration/test_api_routes.py` covering health, configuration, farmer CRUD, spatial clustering, economics, NASA status, harmonization, and daily/weekly/monthly/annual calendar routes.
- **Test Suite Expansion**: Grew verified automated test suite from 32 to 44 passing tests ($100\%$ pass rate).

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
