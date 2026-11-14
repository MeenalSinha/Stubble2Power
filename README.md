# Stubble2Power

**Satellite Intelligence. Sustainable Agriculture. Clean Energy.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-336791.svg)](https://postgis.net/)
[![NASA Space Apps](https://img.shields.io/badge/NASA_Space_Apps-Challenge_09-0B3D91.svg)](https://www.spaceappschallenge.org/)
[![Security: PBKDF2--SHA256](https://img.shields.io/badge/Security-PBKDF2--SHA256-green.svg)](docs/SECURITY_THREAT_MODEL.md)
[![Compliance: DPDP Act 2023](https://img.shields.io/badge/Compliance-DPDP_Act_2023-blue.svg)](docs/PRIVACY_GOVERNANCE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Executive Overview

**Stubble2Power** is an enterprise-grade Earth Observation, Agricultural Waste Logistics, and Clean Energy platform. It addresses the annual crop residue burning crisis in Northern India by bridging satellite active fire intelligence with decentralized mobile bio-refineries.

The platform unites three core pillars:
1. **NASA Satellite Fire Intelligence**: Harmonizes NASA FIRMS MODIS (Terra & Aqua) and VIIRS (NOAA-20, Suomi-NPP, NOAA-21) active fire observations into a coherent spatial and temporal burning activity calendar with statistical anomaly detection and agricultural context classification.
2. **Agricultural Waste Management Intelligence**: Connects farm parcel coordinates with on-site mobile bio-refinery routing (2-opt TSP road routing), crop-specific residue estimation, techno-economic DCF modeling, and cradle-to-grave LCA carbon accounting (Verra VM0044/Puro.earth additionality).
3. **Enterprise Identity, Governance & Privacy Platform (Phases 13 & 14)**: Features dedicated role-oriented workspaces (7 standard roles), multi-tenant cooperative isolation, salted PBKDF2-SHA256 authentication, HMAC-SHA256 JWT sessions, fine-grained server-side RBAC, purpose-bound DPDP Act 2023 consent tracking, statutory data subject requests, 2-decimal geospatial location obfuscation (~1.1 km blur for public access), immutable audit logs, and multilingual localization (English, Hindi, Punjabi).

### Selected NASA Space Apps Challenge
- **Challenge 09: Harmonization of MODIS and VIIRS Hot Spots**
- **Challenge Portal**: [https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/)
- **NASA FIRMS Documentation**: [https://firms.modaps.eosdis.nasa.gov/api/](https://firms.modaps.eosdis.nasa.gov/api/)

---

## 🏗️ Platform Architecture

```
Stubble2Power/
├── backend/
│   ├── api/routes/          # RESTful endpoints (health, config, farmers, clustering, economics, nasa, harmonization, calendar)
│   ├── core/
│   │   ├── config/          # Centralized, versioned configuration with literature provenance & validation bounds
│   │   ├── logging/         # Structured logger with automatic secret masking
│   │   └── exceptions/      # Domain exception hierarchy
│   ├── models/              # SQLAlchemy ORM models (PostgreSQL/PostGIS & SQLite)
│   ├── schemas/             # Pydantic validation schemas
│   ├── repositories/        # Database abstraction layer
│   ├── services/
│   │   ├── nasa/            # NASA FIRMS API client with backoff and retry
│   │   ├── fire/            # Normalization, quality control, deduplication, quarantine
│   │   ├── harmonization/   # Scientific MODIS-VIIRS cross-sensor association & calibrated FRP
│   │   ├── calendar/        # Dynamic daily, weekly, monthly, annual activity calendar
│   │   ├── farmers/         # Farmer CRUD, validation, CSV import/export
│   │   ├── clustering/      # Geodesic Haversine K-Means route optimization
│   │   ├── economics/       # Unit economics, breakeven tonnage, logistics savings
│   │   ├── environmental/   # Avoided CO2, coal replacement, EPA social equivalents
│   │   └── geospatial/      # Great-circle calculations, bounding box validation, grid binning
│   └── main.py              # FastAPI application entrypoint with OpenAPI docs
│
├── frontend/
│   └── streamlit_app/
│       └── styles/          # Glassmorphism theme CSS
│
├── database/
│   ├── migrations/          # Alembic database migration scripts
│   └── seeds/               # Reference datasets: benchmark farmers, satellite fire observations, AOIs
│
├── tests/
│   ├── unit/                # Core calculation and service unit tests
│   ├── integration/         # Database persistence, NASA ingestion, and harmonization tests
│   └── regression/          # Mathematical parity tests verifying legacy formula accuracy
│
├── docs/                    # Architecture, Database, NASA Data, Harmonization, and Config specifications
├── app.py                   # Upgraded multi-system Streamlit frontend
├── Dockerfile               # Multi-stage container definition
├── docker-compose.yml       # Production deployment with PostGIS, FastAPI, and Streamlit
└── requirements.txt         # Production Python dependencies
```

---

## ✨ Key Capabilities

### System A: NASA Fire Intelligence
- **NASA FIRMS Integration**: Native support for `MODIS_NRT`, `MODIS_SP`, `VIIRS_NOAA20_NRT`, `VIIRS_SNPP_NRT`, and `VIIRS_NOAA21_NRT`.
- **Quality Control Pipeline**: UTC normalization, coordinate range validation, brightness temperature thresholding, and quarantine auditing.
- **Scientific Harmonization Engine**:
  - Reconciles MODIS (1km) and VIIRS (375m) footprint disparities.
  - Groups detections into configurable spatial grid cells (default: 0.05° ≈ 5 km).
  - Matches cross-sensor candidate pairs within 1.5 km and 3.0-hour overpass windows.
  - Applies Wooster et al. (2021) empirical Fire Radiative Power (FRP) intercalibration ($\beta = 1.04$).
  - Computes a Normalized Burning Activity Index (0 to 100) and Sensor Consensus Score (0.0 to 1.0).
- **Historical Burning Activity Calendar**: Continuous daily heatmaps, monthly aggregations, Kharif seasonal peak detection, and data completeness tracking (distinguishes real zero burning from lack of overpass).
- **Advanced Geospatial Map**: Multi-layer Folium mapping showing MODIS (1km red), VIIRS (375m orange), Harmonized Activity Grid (colored by index), and Mobile Bio-Refineries with interactive popups.

### System B: Agricultural Waste Management
- **Persistent Farmer Registry**: Database-backed farm acreage, stubble estimates, harvest dates, and WGS84 coordinates.
- **AI Geodesic Clustering & 2-Opt TSP Routing**: Groups farm locations and solves vehicle routing using 2-Opt edge-swaps with NRIDA PMGSY empirical rural road tortuosity factors.
- **Techno-Economic DCF Modeling**: Simulates briquette production, biochar, direct farmer payments (₹1,800/ton), DCF NPV, IRR, and breakeven tonnages across dynamic scenarios.
- **Cradle-to-Grave Life Cycle Assessment (LCA)**: Quantifies net emissions, displacement of fossil coal, biochar stable soil sequestration, and Verra VM0044/Puro.earth additionality.

### System C: Multi-User Platform, Security & Governance (Phases 13 & 14)
- **Role-Oriented Workspaces**: 7 distinct persona workspaces (`Public Visitor`, `Farmer`, `Field Operator`, `Agricultural Analyst`, `Environmental Analyst`, `Organization Manager`, `System Administrator`) plus `Technical Engine Explorer`.
- **Identity & Session Architecture**: Salted PBKDF2-SHA256 password hashing (100k iterations) and HMAC-SHA256 JWT access & refresh tokens with active session tracking (`UserSession`).
- **Server-Side RBAC & IDOR Prevention**: 32 granular permissions enforced via FastAPI dependencies with object-level ownership checks (`verify_resource_ownership`).
- **Multi-Tenant Organization Isolation**: Row-level tenant partitioning across cooperatives (`PB-BIO-COOP`, `MAPS-MALWA`) with strict cross-tenant denial rules.
- **DPDP Act 2023 Statutory Privacy Compliance**: Purpose-bound consent records (`ConsentRecord`), Data Subject Requests (`DataSubjectRequest`), automated retention sweeps (`DataRetentionPolicy`), and 2-decimal geospatial location obfuscation (~1.1 km blur for public visitors).
- **Multilingual Framework**: Centralized localization supporting English (`en`), Hindi (`hi`), and Punjabi (`pa`).
- **Zero-Emoji Professional UX**: Modern agricultural glassmorphism conforming to WCAG 2.2 AA accessibility standards.

---

## 🔒 Non-Negotiable Engineering Standards

1. **Nothing Hardcoded**: All economic parameters, yields, prices, haulage distances, emission factors, and sensor tolerances are managed through `ConfigManager` with documented citations and units. No magic numbers remain in source code.
2. **No Fake Functionality**: Satellite observations, consensus scores, and analytics reflect verified database records. When NASA credentials are unconfigured, clear diagnostic status is reported.
3. **Preserved Functionality**: All five original application sections (Home, Data Input, Clustering, Economics, Executive Dashboard) are preserved and upgraded.
4. **Complete Test Suite**: Automated unit, integration, and regression tests cover all domain services (100% pass rate).

---

## 🚀 Quick Start & Execution

### 1. Prerequisites
- Python 3.11+
- Virtual environment tool (`venv`)
- (Optional) Docker and Docker Compose

### 2. Environment Setup
Clone the repository and create an isolated virtual environment:
```bash
git clone https://github.com/your-org/Stubble2Power.git
cd Stubble2Power

python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

Create your `.env` configuration from template:
```bash
cp .env.example .env
```
*(Optional: Request a free NASA FIRMS MAP_KEY at [https://firms.modaps.eosdis.nasa.gov/api/map_key/](https://firms.modaps.eosdis.nasa.gov/api/map_key/) and add it to `NASA_FIRMS_MAP_KEY` in `.env`).*

### 3. Initialize Database & Seed Benchmark Data
```bash
# Windows PowerShell:
$env:PYTHONPATH="."
python database/seeds/seed_data.py

# Linux / macOS:
PYTHONPATH=. python database/seeds/seed_data.py
```

### 4. Run Automated Test Suite
```bash
pytest -v
```
*Executes all 81 automated unit, integration, regression, and pipeline tests across Phases 0 through 12 with 100% pass rate.*

### 5. Launch Application

#### Option A: Streamlit Unified Frontend (Default)
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

#### Option B: FastAPI Backend API Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Access interactive OpenAPI documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

#### Option C: Production Docker Compose
```bash
docker compose up -d --build
```
Provisions PostgreSQL 16 with PostGIS 3.4, FastAPI backend on port 8000, and Streamlit on port 8501.

---

## 📚 Technical Documentation Directory

### Architecture & Schemas
- [System Architecture](docs/ARCHITECTURE.md)
- [Database Schema & Entity Models](docs/DATABASE.md)
- [REST API Reference (OpenAPI 3.0)](docs/API.md)
- [Configuration Registry & Parameter Provenance](docs/CONFIGURATION.md)
- [Master Emission Factors Registry](docs/EMISSION_FACTORS.md)
- [Engineering Changelog](docs/CHANGELOG.md)

### Earth Observation & Remote Sensing
- [NASA FIRMS Data Integration](docs/NASA_DATA.md)
- [MODIS & VIIRS Scientific Harmonization](docs/HARMONIZATION.md)
- [Seasonal Intelligence & Empirical Fire Profiles](docs/SEASONAL_INTELLIGENCE.md)
- [Statistical Anomaly Detection & Diagnostics](docs/ANOMALY_DETECTION.md)
- [Agricultural Crop Calendars & Phenology](docs/CROP_CALENDAR_METHODOLOGY.md)
- [Land Use Land Cover (LULC) Classification](docs/AGRICULTURAL_DATA_SOURCES.md)

### Agricultural Intelligence & Supply Chain (Phases 10–12)
- [Farmer & Farm Management Architecture](docs/FARMER_AND_FARM_MANAGEMENT.md)
- [Biomass Estimation & Inventory Methodology](docs/BIOMASS_METHODOLOGY.md)
- [Mobile Bio-Refinery Fleet & Technology](docs/MOBILE_BIOREFINERY.md)
- [Rural Road Network Routing & Tortuosity Optimization](docs/ROUTE_OPTIMIZATION.md)
- [Techno-Economic Feasibility & Financial Methodology](docs/ECONOMIC_METHODOLOGY.md)
- [Life Cycle Assessment (LCA) & Net Climate Accounting](docs/ENVIRONMENTAL_METHODOLOGY.md)

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for details.
