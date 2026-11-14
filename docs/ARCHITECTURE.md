# Stubble2Power - System Architecture Documentation

## 1. Architectural Vision & Design Principles

Stubble2Power is an enterprise-grade Earth Observation and Agricultural Waste Logistics platform designed to solve agricultural residue burning while unlocking sustainable economic returns for farmers through decentralized mobile bio-refineries.

The platform unites two previously isolated intelligence domains:
1. **NASA Satellite Fire Intelligence**: Near-real-time and historical fire observation ingestion, sensor quality control, and scientific cross-sensor harmonization (MODIS and VIIRS).
2. **Agricultural Waste Management & Mobile Logistics**: Farm coordinate registration, biomass availability estimation, geodesic K-Means clustering, route optimization, unit economics simulation, and carbon dividend calculation.

### Design Principles
- **Separation of Concerns**: Presentation (Streamlit / REST API) is strictly decoupled from business logic and database access.
- **Rule 1 - Nothing Hardcoded**: All scientific, economic, geographical, and operational values are dynamically retrieved from the Configuration Registry with documented provenance, citations, and validation bounds.
- **Rule 2 - No Fake Functionality**: Satellite observations, harmonization consensus metrics, and economic calculations are derived strictly from genuine database records and validated equations.
- **Extensible Microservice Boundary**: A FastAPI backend provides OpenAPI-documented endpoints enabling headless execution or future React frontends.

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------------+
|                                    USER INTERFACES                                      |
|  Streamlit UI (Glassmorphism Dashboard)   |   OpenAPI Swagger Documentation (/docs)     |
+-----------------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------------+
|                                    API LAYER (FastAPI)                                  |
|  /api/health       /api/config        /api/farmers      /api/clustering                 |
|  /api/economics    /api/nasa          /api/harmonization /api/calendar                  |
+-----------------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------------+
|                                   SERVICES LAYER                                        |
|  +------------------------+  +--------------------------+  +--------------------------+ |
|  |     NASAClient         |  |   QualityControlService  |  |   HarmonizationEngine    | |
|  | (FIRMS API, Retry)     |  | (Normalization, QA/QC)   |  | (Association, Gridding)  | |
|  +------------------------+  +--------------------------+  +--------------------------+ |
|  +------------------------+  +--------------------------+  +--------------------------+ |
|  |     FarmerService      |  |    ClusteringService     |  |    EconomicsService      | |
|  | (CRUD, CSV Import)     |  | (Haversine K-Means)      |  | (Unit Economics & Opex)  | |
|  +------------------------+  +--------------------------+  +--------------------------+ |
|  +------------------------+  +--------------------------+  +--------------------------+ |
|  |  EnvironmentalService |  | CalendarAggregationSvc   |  |    GeospatialService     | |
|  | (CO2 & Coal Multipliers|  | (Daily/Monthly Summary)  |  | (Haversine, Bounding Box)| |
|  +------------------------+  +--------------------------+  +--------------------------+ |
+-----------------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------------+
|                                 CORE & REPOSITORY LAYER                                 |
|  ConfigManager (Metadata, Provenance)  |  Structured Logger (Secret Masking)            |
|  FarmerRepository                      |  SatelliteRepository                           |
|  HarmonizationRepository               |  ConfigRepository                              |
+-----------------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------------+
|                                   DATA STORAGE LAYER                                    |
|  PostgreSQL 16 + PostGIS 3.4 (Production)  /  SQLite 3.50+ (Portable Test / Dev)        |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Core Modules & Responsibilities

### 3.1 Backend Core (`backend/core/`)
- `config/settings.py`: Implements `ConfigManager` and `AppSettings`. Enforces minimum/maximum validation bounds on all scientific and economic variables.
- `logging/logger.py`: Custom logging filter scrubbing sensitive tokens (e.g. `MAP_KEY`, passwords, database credentials) from all outputs.
- `exceptions/base.py`: Domain exception hierarchy (`Stubble2PowerException`, `ConfigurationError`, `NASAAPIError`, `ValidationError`).

### 3.2 Services (`backend/services/`)
- `nasa/client.py`: High-reliability client for NASA FIRMS REST API with exponential backoff and timeout handling.
- `nasa/ingestion_service.py`: Orchestrates ingestion jobs with lifecycle tracking (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
- `fire/quality_service.py`: Standardizes raw satellite fields, validates coordinates and temperatures, and quarantines corrupted records.
- `harmonization/engine.py`: Performs spatial gridding (0.05°), temporal alignment (3.0h), cross-sensor footprint matching, and calibrated FRP calculations.
- `calendar/service.py`: Aggregates continuous daily, monthly, and seasonal burning metrics while distinguishing real zero burning from missing overpass coverage.
- `farmers/service.py`: Validates farmer identities, land acreage, and stubble tonnage; provides CSV import/export.
- `clustering/service.py`: Performs K-Means clustering using great-circle Haversine distances rather than planar degree approximations.
- `economics/service.py`: Computes unit economics, breakeven tonnage, and decentralized logistics savings.
- `environmental/service.py`: Converts avoided residue burning into EPA/IPCC emissions and social equivalencies.
- `seasonal/`: Derives multi-year parametric & robust historical baselines and empirical seasonal activity curves (Phase 8).
- `anomaly/`: Detects statistical surges using Z-Score, robust MAD, and EWMA with diagnostic explanation JSON (Phase 8).
- `agriculture/`: Implements PAU/ICAR crop calendars, ESA/Bhuvan LULC zones, and Bayesian context classification (Phase 9).
- `farms/`: Manages spatial parcel boundaries, acreage conservation, crop cycles, and measured harvest records (Phase 10).
- `biomass/`: Executes mathematical residue deductions (RPR, 25% soil retention, fodder, handling loss) and inventory lifecycle auditing (Phase 10).
- `deployment/`: Manages mobile bio-refinery fleet readiness, capacity-constrained dispatch, and unserved farm audits (Phase 11).
- `routing/`: Implements NRIDA rural road network tortuosity modeling (1.35x) and multi-stop vehicle routing (Phase 11).
- `economics/financial_engine.py`: Comprehensive capital budgeting, break-even, multi-year DCF (NPV/IRR), sensitivity tornado modeling, and separated physical revenues (Phase 12).
- `environmental/lca_engine.py`: Cradle-to-grave Life Cycle Assessment using IPCC AR6 GWP, CEA India coal displacement, biochar 100-year carbon permanence, and carbon-credit eligibility separation (Phase 12).
- `auth/`: Authentication, salted PBKDF2 password hashing, HMAC-SHA256 JWT sessions, and tenant isolation (Phase 13 & 14).
- `privacy/`: Digital Personal Data Protection (DPDP) Act 2023 compliance, purpose-bound consents, statutory DSRs, and 2-decimal location obfuscation (Phase 13 & 14).
- `audit/`: Append-only audit trails, security event monitoring, and statutory retention sweeps (Phase 14).
- `user_experience/`: Personalization preferences, in-app notifications, and auditable dossier generation (Phase 13).

### 3.3 Security & Identity Architecture (`backend/core/security/`)
- `password.py`: Salted PBKDF2-SHA256 hashing with 100,000 iterations via passlib.
- `auth.py`: HMAC-SHA256 JWT issuance, standardized epoch timestamps (`time.time()`), and token hashing for session tracking.
- `rbac.py`: 7 standardized platform roles and 32 granular permissions with server-side dependency enforcement.

---

## 4. Security & Configuration Guarantees
- Secrets (NASA `MAP_KEY`, JWT secret, database credentials) are read exclusively from environment variables or `.env` and are never hardcoded.
- Input validation via Pydantic schemas prevents malformed coordinates, negative tonnages, or out-of-range dates.
- SQL injection protection is enforced through SQLAlchemy ORM parameter binding.
- Zero-trust multi-tenancy enforces strict cross-tenant data access denials.
- Geospatial privacy filter obfuscates farm parcel coordinates to 2 decimal places (~1.1 km) for public visitors under the DPDP Act 2023.
