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

---

## 4. Security & Configuration Guarantees
- Secrets (NASA `MAP_KEY`, database credentials) are read exclusively from environment variables or `.env` and are never hardcoded.
- Input validation via Pydantic schemas prevents malformed coordinates, negative tonnages, or out-of-range dates.
- SQL injection protection is enforced through SQLAlchemy ORM parameter binding.
