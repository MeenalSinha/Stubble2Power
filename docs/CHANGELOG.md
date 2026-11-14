# Stubble2Power - Engineering Changelog

## [2.5.0] - 2026-11-14

### Phase 15, 16 & 17 Master Release: Comprehensive Testing, Scientific Validation, Production DevOps & Product Release Readiness

#### Phase 15: Comprehensive Testing & Scientific Validation
- **Expanded Test Pyramid**: Scaled automated test suite to **144 tests passed in 20.55s (100% pass rate)** with zero failures across all test suites.
- **Dedicated Scientific Validation Suite (`tests/scientific/`)**:
  - `test_harmonization_validation.py`: Mathematical proof of NASA MODIS–VIIRS spatiotemporal coincidence window ($1.5\text{ km} / 3.0\text{ h}$), Wooster et al. linear FRP cross-calibration ($\beta = 1.040$), Normalized Burned Area Index (NBAI), and multi-sensor consensus scoring.
  - `test_biomass_validation.py`: Rigorous agronomic mass balance validation using Punjab Agricultural University (PAU) Residue-to-Product Ratios (RPR: Paddy 1.15, Wheat 1.30, Cotton 2.50, Maize 1.20, Sugarcane 0.20), moisture equilibrium, and competing fodder deductions.
  - `test_routing_validation.py`: Haversine geodesic validation, PMGSY empirical rural road tortuosity ($\tau = 1.350$), physical diesel consumption modeling ($0.32\text{ L/km}$ base tare), and 2-Opt TSP edge-swap Pareto convergence.
  - `test_economics_validation.py`: Techno-economic mass transformation conservation, multi-year DCF discounting at $10.5\%$ WACC, dynamic break-even capacity, and negative contribution margin boundary protections.
  - `test_lca_validation.py`: ISO 14040/14044 cradle-to-grave LCA accounting verified against IPCC AR6 GWP100 metrics ($\text{CH}_4 = 27.90$, $\text{N}_2\text{O} = 273.00$), open field burning emission factors, thermal coal displacement ($0.98\text{ t }\text{CO}_2\text{e}/\text{t}$), 100-year biochar recalcitrance ($2.20\text{ t }\text{CO}_2\text{e}/\text{t}$), and Verra additionality.
- **Invariants & Security Tests (`tests/unit/test_invariants_and_edge_cases.py`)**: Validated metric tensor scaling, road distance monotonicity, zero-biomass numerical safety, forged JWT token rejection, and location privacy bounding box invariants.
- **Performance & Benchmark Suite (`tests/performance/test_benchmarks.py`)**: Verified that $10,000$ geospatial distance computations execute in $<0.20\text{s}$, 2-Opt routing completes in $<0.30\text{s}$, 50 DCF scenarios evaluate in $<0.50\text{s}$, and 500 JWT cryptographic cycles execute in $<0.25\text{s}$.
- **Fault Tolerance & Recovery Suite (`tests/reliability/test_failure_recovery.py`)**: Validated circuit breakers for NASA 503 Gateway outages, network timeouts, unhandled database rollbacks, and corrupted satellite CSV payloads.
- **End-to-End User Workflows (`tests/e2e/test_complete_user_workflows.py`)**: Implemented 7 full multi-system integration tests covering satellite harmonization, harvest association, biomass estimation, fleet dispatch, DCF/LCA, multi-tenant RBAC, and DPDP Section 6 consent withdrawal exclusion.
- **Scientific Validation Report**: Authored comprehensive documentation in `docs/SCIENTIFIC_VALIDATION.md`.

#### Phase 16: Production Deployment & DevOps
- **Hardened Multi-Stage Container Image (`Dockerfile`)**: Implemented builder stage compiling wheel cache and minimal runner stage using non-root unprivileged system user `stubble_app` (UID/GID 10001) with internal container healthchecks.
- **Zero-Host Exposure Production Compose (`docker-compose.prod.yml`)**: PostgreSQL/PostGIS port 5432 is strictly internal to `s2p-prod-network` (zero public host exposure), fail-closed secret injection, container healthchecks, and strict CPU/Memory resource limits.
- **Automated CI/CD Pipeline (`.github/workflows/ci-cd.yml`)**: 5-stage GitHub Actions pipeline featuring code quality checks (flake8, black, ruff), static application security testing (bandit, pip-audit), automated test suite execution (144 tests with XML coverage reports), multi-stage Docker build, and staging deployment.
- **Automated Backup & Restore Infrastructure**:
  - `scripts/backup_db.py`: Backs up SQLite and PostgreSQL, creates timestamped encrypted gzip archives, computes cryptographic SHA-256 checksums, and enforces retention pruning.
  - `scripts/restore_db.py`: Verifies SHA-256 checksums, restores database state safely, and executes post-restore smoke test queries to certify database integrity.
- **Infrastructure Runbooks**: Authored `docs/DEPLOYMENT_ARCHITECTURE.md` and `docs/DEPLOYMENT_RUNBOOK.md`.

#### Phase 17: Documentation, Release & Product Readiness
- **Operational User Manuals (`docs/USER_GUIDES.md`)**: Complete step-by-step operating guides for all 5 enterprise roles (Farmer, Fleet Logistics Operator, Plant Manager, Environmental Analyst, System Administrator).
- **Third-Party Notices (`docs/THIRD_PARTY_NOTICES.md`)**: Full legal attributions and licenses for NASA FIRMS, OpenStreetMap, Python dependencies, and PostGIS.
- **Operational Handover (`docs/OPERATIONAL_HANDOVER.md`)**: Production SLA, incident response escalation pathways, monitoring metrics, and routine maintenance schedules.
- **Release Documentation (`docs/RELEASE_NOTES_v2.5.0.md`)**: Formal product release notes certifying production readiness.
- **Master README Update**: Comprehensive platform documentation with professional typography and zero decorative emojis.

---

## [2.4.0] - 2026-11-14

### Phase 13 & 14 Master Release: Enterprise Multi-User Experience, Security Architecture, RBAC & DPDP Privacy Governance

#### Phase 10–12 Comprehensive Audit & Hardening
- **Configuration Registry Completeness**: Added 26+ parameters to `ConfigManager` covering baseline yields, RPR ratios, retention fractions, transit speeds, default CAPEX/OPEX, and security tokens.
- **Biomass Estimation Normalization**: Replaced silent paddy fallback with crop-specific dictionary lookup and transparent date scheduling fallback notes.
- **Routing Optimization**: Validated genuine 2-Opt local search TSP edge-swap optimization with NRIDA PMGSY empirical rural road network tortuosity factors.
- **Financial Simulation Safeguards**: Added robust non-positive contribution margin handling (`break_even_tons = 0.0`) and non-positive profit protections (`payback_years = 0.0`, `roi_pct = 0.0`).
- **LCA Carbon Credit Separation**: Integrated modeled transport diesel fuel consumption and explicitly separated biogenic burning CO2 from high-integrity additionality (Verra VM0044/Puro.earth).

#### Phase 13: Complete User Experience & Multi-User Platform
- **Role-Oriented Workspaces**: Implemented 7 distinct persona workspaces (`Public Visitor`, `Farmer`, `Field Operator`, `Agricultural Analyst`, `Environmental Analyst`, `Organization Manager`, `System Administrator`).
- **Preserved Technical Engine Explorer**: Seamlessly retained all 12 deep technical engines from Phases 0–12 for authorized analysts and administrators.
- **Centralized Multilingual Localization Framework**: Engineered `frontend/streamlit_app/localization/i18n.py` providing verified UI strings in English (`en`), Hindi (`hi`), and Punjabi (`pa`).
- **Strict Zero-Emoji Professional UX**: Completely eliminated decorative emojis across all UI headers, navigation bars, buttons, and badges in compliance with Rules 7 & 9, replacing them with standardized text badges (`[OK]`, `[ALERT]`, `[WARN]`, `[VERIFIED]`).
- **WCAG 2.2 AA Accessibility**: Verified 10.4:1 contrast ratios on primary text (`#1e462d` on `#ffffff`), visible keyboard focus indicators, color-independent status indicators, and screen-reader data table fallbacks.
- **Personalization Services**: Created `UserPreference`, `Notification`, and `SavedReport` entities and REST APIs under `/api/user/`.

#### Phase 14: Security, Privacy & Governance
- **Cryptographic Identity Architecture**: Implemented salted PBKDF2-SHA256 password hashing (100,000 rounds) via `passlib` and HMAC-SHA256 JWT access and refresh tokens with standardized UNIX epoch timestamps (`time.time()`).
- **Active Session Governance**: Implemented `UserSession` tracking SHA-256 token hashes for instant session invalidation and logout.
- **Server-Side RBAC & IDOR Prevention**: Implemented 32 granular permissions with FastAPI dependencies (`require_permission`, `require_role`) and object-level ownership verification (`verify_resource_ownership`).
- **Multi-Tenant Organization Isolation**: Enforced row-level tenant partitioning on `organization_id` with cross-tenant denial rules (`verify_organization_access`).
- **DPDP Act 2023 Statutory Privacy Compliance**:
  - Purpose-bound consent lifecycle (`ConsentRecord`) supporting instant granting and withdrawal across `BIOMASS_AGGREGATION`, `SATELLITE_FIRE_CORRELATION`, `LOGISTICS_DISPATCH`, and `DIRECT_PAYMENT`.
  - Data Subject Request management (`DataSubjectRequest`) supporting `ACCESS`, `CORRECTION`, `ERASURE`, and `EXPORT`.
  - Geospatial location privacy filter obfuscating farm parcel coordinates to 2 decimal places ($\approx 1.1\text{ km}$ resolution) on public interfaces while preserving exact coordinates for owners and dispatchers.
  - Statutory data retention sweeps (`DataRetentionPolicy`) enforcing 730-day audit log retention and 30-day session purges.
- **Immutable Audit Trail & Monitoring**: Implemented append-only `AuditLog` and `SecurityEvent` models and services.
- **Comprehensive Security Documentation**: Authored `docs/SECURITY_THREAT_MODEL.md` (STRIDE analysis), `docs/INCIDENT_RESPONSE.md`, `docs/IDENTITY_AND_AUTHENTICATION.md`, `docs/AUTHORIZATION_MODEL.md`, `docs/ORGANIZATION_ISOLATION.md`, `docs/DATA_CLASSIFICATION.md`, `docs/PRIVACY_GOVERNANCE.md`, `docs/UX_DESIGN_SYSTEM.md`, `docs/USER_ROLES_AND_WORKFLOWS.md`, `docs/ACCESSIBILITY.md`, and `docs/SECURITY_TESTING.md`.

#### Automated Quality Verification
- Total automated test suite expanded to **101 tests passed in 10.34s** (100% pass rate).

---

## [2.3.0] - 2026-11-14

### Phase 10, 11 & 12 Master Release: Full Biomass Supply Chain, Fleet Logistics, Techno-Economics & LCA Environmental Intelligence

#### Phase 10: Farmer, Farm & Biomass Intelligence
- **Farm Entity Architecture**: Created `Farm` (spatial parcel, centroid coordinates, boundary GeoJSON, soil classification, ownership status) and `FarmCrop` (seasonal crop tracking, sowing/harvest dates, acreage conservation guard).
- **Empirical Harvest Tracking**: Implemented `HarvestRecord` capturing empirical grain harvest yields (combine harvester, Super SMS, manual) and grain moisture content.
- **Mathematical Biomass Estimation Engine**: Implemented `BiomassEstimationService` incorporating literature-calibrated Residue-to-Product Ratios (Paddy 1.50, Wheat 1.30, Cotton 2.80), mandatory 25% soil organic carbon retention, 55-60% competing dairy fodder deduction for wheat, and 8% mechanical handling loss.
- **Audited Inventory Lifecycle**: Implemented `BiomassInventoryService` tracking transitions across `ESTIMATED`, `CONFIRMED`, `COMMITTED`, `COLLECTED`, `STORED`, `ALLOCATED`, and `PROCESSED`.
- **Double-Allocation Guard**: Engineered a database-level transaction guard preventing over-allocation of biomass across deployment plans.
- **REST APIs**: Mounted `/api/farms/`, `/api/farms/{id}/crops`, `/api/farms/crops/{id}/harvest`, `/api/biomass/estimate`, `/api/biomass/estimates/{id}`, `/api/biomass/inventory/transaction`, and `/api/biomass/summary`.
- **UI Dashboard**: Built Streamlit modules `Farm & Cultivation Intelligence` and `Biomass Availability & Inventory` with Folium parcel map and lifecycle funnel.

#### Phase 11: Mobile Bio-Refinery & Fleet Logistics Intelligence
- **Fleet Registry & Capability Management**: Implemented `MobileRefineryService` managing trailer-mounted briquetters ($2.5\text{ t/h}$, $25\text{ t/day}$) and slow pyrolysis rigs ($1.5\text{ t/h}$, $15\text{ t/day}$), auxiliary generator diesel consumption ($4.5\text{ L/t}$), hourly operating costs, and home depot coordinates.
- **NRIDA Rural Road Network Routing**: Implemented `RoadNetworkService` with PMGSY calibrated rural road tortuosity factor ($\tau = 1.35\times\text{geodesic}$), $35\text{ km/h}$ average tractor transit speed, and $0.32\text{ L/km}$ diesel consumption rate.
- **Multi-Unit Deployment Planner**: Implemented `DeploymentPlannerService` solving capacity-constrained vehicle dispatch across target farm clusters respecting daily throughput, campaign days, and maximum operating radii.
- **Vehicle Routing Problem (CVRP)**: Implemented nearest-neighbor 2-opt vehicle routing with multi-stop sequencing starting and returning to regional depots.
- **Transparent Unserved Audit**: Implemented transparent logging and UI reporting for any farms that cannot be serviced due to fleet capacity limits or radius constraints.
- **REST APIs**: Mounted `/api/mobile-units/`, `/api/mobile-units/{id}/status`, `/api/deployments/plan`, `/api/deployments/`, `/api/deployments/{id}`, `/api/deployments/{id}/cancel`, and `/api/deployments/{id}/routes`.
- **UI Dashboard**: Built Streamlit module `Mobile Bio-Refinery & Fleet Logistics` with fleet registry, interactive deployment planner, and Folium route sequencing visualizer.

#### Phase 12: Advanced Techno-Economics & LCA Environmental Impact Intelligence
- **Techno-Economic Modeling Engine**: Implemented `FinancialEngineService` calculating CAPEX ($25\text{ Lakhs/unit}$, 7-year straight-line depreciation), OPEX, farmer procurement incentive payments ($\text{INR } 1,500\text{/ton}$), logistics transport costs, and auxiliary processing fuel/labor.
- **Physical Revenue Separation**: Strictly isolated operational cash revenue from physical product sales (briquettes at $\text{INR } 6,000\text{/t}$ and biochar at $\text{INR } 15,000\text{/t}$), prohibiting speculative carbon credit dependence.
- **Capital Budgeting Metrics**: Derived break-even tonnage, gross profit, net margin %, simple payback period, ROI %, NPV (using $10.5\%$ IREDA WACC discount rate), and Internal Rate of Return (IRR).
- **Sensitivity Tornado Analysis**: Automated parameter elasticity calculations across briquette price, biochar price, farmer payout, and retail diesel price ($\pm 10\%$ and $\pm 20\%$).
- **Cradle-to-Grave Life Cycle Assessment (LCA)**: Implemented `LifeCycleAssessmentService` with IPCC AR6 WG1 100-year GWP metrics ($\text{CH}_4=27.9, \text{N}_2\text{O}=273$) comparing open-field burning against mobile densification.
- **Fossil Coal Displacement**: Modeled industrial boiler thermal substitution ($0.82\text{ kg coal/kg briquette}$) displacing sub-bituminous coal ($2,120\text{ kg CO}_2\text{/ton}$) based on CEA Database v19.0.
- **Biochar 100-Year Carbon Permanence**: Modeled $72.0\%$ persistent soil carbon storage in slow pyrolysis biochar.
- **Net Benefit Ratio**: Verified $>1.8\times\text{--}2.2\times$ net environmental benefit ratio relative to baseline burning.
- **Carbon-Credit Eligibility Separation**: Explicitly separated biogenic short-cycle burning $\text{CO}_2$ from verifiable additionality (avoided non-$\text{CO}_2$ gases, coal displacement, and biochar permanence minus project fossil emissions) conforming to Verra VM0044 and Puro.earth.
- **REST APIs**: Mounted `/api/economics/scenario`, `/api/economics/scenarios`, `/api/economics/compare`, `/api/economics/scenarios/{id}/sensitivity`, `/api/environmental/lca`, `/api/environmental/assessments`, and `/api/environmental/system-boundary`.
- **UI Dashboards**: Built Streamlit modules `Techno-Economic Decision Support` and `LCA Environmental Impact Assessment` with financial waterfall, scenario comparisons, sensitivity tornado chart, and GHG balance bar visualizers.

#### Automated Test Suite & Quality Verification
- Total automated tests expanded to **81 passing tests** (100% pass rate in 12.42s).
- Verified full Docker Compose stack with PostGIS database, FastAPI backend, and Streamlit frontend.

---

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
