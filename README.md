# Stubble2Power

**Satellite Intelligence. Sustainable Agriculture. Clean Energy.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-336791.svg)](https://postgis.net/)
[![NASA Space Apps](https://img.shields.io/badge/NASA_Space_Apps-Challenge_09-0B3D91.svg)](https://www.spaceappschallenge.org/)
[![Test Suite](https://img.shields.io/badge/Tests-145%20Passed%20(100%25)-brightgreen.svg)](docs/SCIENTIFIC_VALIDATION.md)
[![Security: PBKDF2--SHA256](https://img.shields.io/badge/Security-PBKDF2--SHA256-green.svg)](docs/SECURITY_THREAT_MODEL.md)
[![Privacy: DPDP Act 2023 Controls](https://img.shields.io/badge/Privacy-DPDP_Act_2023_Controls-blue.svg)](docs/PRIVACY_GOVERNANCE.md)
[![Release: v2.5.0](https://img.shields.io/badge/Release-v2.5.0-blue.svg)](docs/RELEASE_NOTES_v2.5.0.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Executive Overview

**Stubble2Power** is an enterprise-grade Earth Observation, Agricultural Waste Logistics, and Clean Energy decision-support platform. It addresses the annual crop residue burning crisis in Northern India by bridging satellite active fire intelligence with decentralized mobile bio-refineries.

The platform unites three core pillars:
1. **NASA Satellite Fire Intelligence**: Harmonizes NASA FIRMS MODIS (Terra & Aqua) and VIIRS (NOAA-20, Suomi-NPP, NOAA-21) active fire observations into a coherent spatial and temporal burning activity calendar with statistical anomaly detection and agricultural context classification.
2. **Agricultural Waste Management Intelligence**: Connects farm parcel coordinates with on-site mobile bio-refinery routing (2-Opt TSP road routing), crop-specific residue estimation, techno-economic DCF modeling, and cradle-to-grave LCA carbon accounting (Verra VM0044/Puro.earth additionality).
3. **Enterprise Identity, Governance, DevOps & Testing Platform (Phases 13 to 17)**: Features dedicated role-oriented workspaces (7 standard roles), multi-tenant cooperative isolation, salted PBKDF2-SHA256 authentication, HMAC-SHA256 JWT sessions, fine-grained server-side RBAC, purpose-bound DPDP Act 2023 consent tracking, 145 automated tests with 100% pass rate, multi-stage non-root container deployment, automated database backups with AES-128-CBC authenticated encryption and SHA-256 verification, and multilingual localization (English, Hindi, Punjabi).

### Selected NASA Space Apps Challenge
- **Challenge 09: Harmonization of MODIS and VIIRS Hot Spots**
- **Challenge Portal**: [https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/)
- **NASA FIRMS Documentation**: [https://firms.modaps.eosdis.nasa.gov/api/](https://firms.modaps.eosdis.nasa.gov/api/)

---

## Platform Architecture

```
Stubble2Power/
├── backend/
│   ├── api/routes/          # 21 RESTful route modules (Auth, NASA, Harmonization, Logistics, Economics, LCA, Privacy)
│   ├── core/
│   │   ├── config/          # Centralized, versioned configuration with literature provenance & validation bounds
│   │   ├── logging/         # Structured logger with automatic secret masking
│   │   ├── exceptions/      # Domain exception hierarchy
│   │   └── security/        # PBKDF2 password hashing, JWT management, RBAC matrices
│   ├── models/              # SQLAlchemy ORM models (PostGIS & SQLite with immutable audit hooks)
│   ├── schemas/             # Pydantic validation schemas with fail-closed bounds
│   ├── repositories/        # Database abstraction layer
│   ├── services/
│   │   ├── nasa/            # NASA FIRMS API client with backoff and retry
│   │   ├── fire/            # Normalization, quality control, deduplication, quarantine
│   │   ├── harmonization/   # Scientific MODIS-VIIRS cross-sensor association & calibrated FRP
│   │   ├── calendar/        # Dynamic daily, weekly, monthly, annual activity calendar
│   │   ├── seasonal/        # 5-year rolling baseline & statistical anomaly detection
│   │   ├── agriculture/     # Land-use masking, crop calendar classification
│   │   ├── biomass/         # PAU agronomic biomass estimation & mass balances
│   │   ├── deployment/      # Capacity-constrained fleet deployment planner
│   │   ├── logistics/       # 2-Opt TSP vehicle routing with PMGSY road tortuosity
│   │   ├── economics/       # Multi-year DCF, WACC discounting, and break-even analysis
│   │   ├── environmental/   # IPCC AR6 cradle-to-grave Life Cycle Assessment (LCA)
│   │   ├── privacy/         # DPDP consent tracking, DSR processing, geospatial obfuscation
│   │   └── audit/           # Immutable audit trails and security event logging
│   └── main.py              # FastAPI application entrypoint with OpenAPI docs (v2.5.0)
│
├── frontend/
│   ├── streamlit_app/
│   │   ├── components/      # Glassmorphism UI components (cards, metrics, maps)
│   │   ├── localization/    # Multilingual localization engine (English, Hindi, Punjabi)
│   │   ├── styles/          # WCAG 2.2 AA compliant glassmorphism theme CSS
│   │   └── workspaces/      # 7 Persona workspaces + Technical Engine Explorer
│   └── app.py               # Main Streamlit interactive application
│
├── database/
│   ├── migrations/          # Alembic database migration scripts
│   └── seeds/               # Reference datasets: benchmark farmers, satellite fire observations, AOIs
│
├── scripts/
│   ├── backup_db.py         # Automated SQLite & PostgreSQL backup with AES-128-CBC encryption and SHA-256 integrity
│   └── restore_db.py        # Automated restore utility with cryptographic validation and smoke testing
│
├── .github/workflows/
│   └── ci-cd.yml            # 5-Stage GitHub Actions CI/CD pipeline
│
├── tests/
│   ├── unit/                # Core calculation and service unit tests (invariants, config, models)
│   ├── integration/         # Database persistence, NASA ingestion, and harmonization tests
│   ├── regression/          # Mathematical parity tests verifying legacy formula accuracy
│   ├── scientific/          # Peer-reviewed validation tests (Harmonization, Biomass, Routing, Economics, LCA)
│   ├── performance/         # High-throughput benchmarks (Geospatial, 2-Opt, DCF, JWT)
│   ├── reliability/         # Fault tolerance & circuit breaker tests (NASA 503, timeouts, DB rollback)
│   └── e2e/                 # 7 End-to-end complete user workflow integration tests
│
├── docs/                    # Architecture, Scientific Validation, Runbooks, User Guides, and API specs
├── Dockerfile               # Hardened multi-stage non-root container image
├── docker-compose.yml       # Development Docker Compose specification
├── docker-compose.prod.yml  # Production Docker Compose specification (zero host DB port exposure)
└── requirements.txt         # Production Python dependencies
```

---

## Key Capabilities Across Phases 0 to 17

### System A: NASA Fire Intelligence (Phases 0 to 9)
- **NASA FIRMS Integration**: Native support for `MODIS_NRT`, `MODIS_SP`, `VIIRS_NOAA20_NRT`, `VIIRS_SNPP_NRT`, and `VIIRS_NOAA21_NRT`.
- **Quality Control Pipeline**: UTC normalization, coordinate range validation, brightness temperature thresholding, and quarantine auditing.
- **Scientific Harmonization Engine (Challenge 09)**:
  - Reconciles MODIS (1km) and VIIRS (375m) footprint disparities.
  - Spatiotemporal coincidence matching within $1.5\text{ km}$ and $3.0\text{ hours}$.
  - Applies Wooster et al. (2021) linear Fire Radiative Power (FRP) cross-calibration ($\beta = 1.040$).
  - Computes Normalized Burned Area Index (NBAI) and multi-sensor consensus scoring ($0.0$ to $1.0$).
- **Historical Burning Activity Calendar**: Daily heatmaps, monthly aggregations, Kharif seasonal peak detection, and data completeness tracking.
- **Statistical Anomaly Detection**: 5-year rolling baselines with robust Median Absolute Deviation (MAD) isolating unusual spikes ($Z \ge 2.0$).
- **Agricultural Land-Use Intelligence**: Remote sensing land-cover masking distinguishing agricultural burning from forest/industrial fires.

### System B: Agricultural Waste Management & Clean Energy (Phases 10 to 12)
- **Farmer & Farm Parcel Management**: Database-backed land parcels, soil classification, harvest records, and WGS84 coordinates.
- **Mathematical Biomass Estimation**: Punjab Agricultural University (PAU) Residue-to-Product Ratios (Paddy 1.15, Wheat 1.30, Cotton 2.50), moisture equilibrium, and competing livestock fodder deductions.
- **Biomass Inventory Funnel**: Audited transitions across `ESTIMATED`, `CONFIRMED`, `COMMITTED`, `COLLECTED`, `STORED`, `ALLOCATED`, and `PROCESSED` with double-allocation prevention.
- **Mobile Bio-Refinery Fleet Deployment**: Fleet registry with hourly capacities, daily operating limits, and capacity-constrained multi-unit dispatching.
- **Vehicle Routing Optimization**: Nearest-neighbor 2-Opt TSP edge-swap heuristic with NRIDA PMGSY rural road network tortuosity factors ($\tau = 1.350$) and diesel physics modeling.
- **Techno-Economic DCF Modeling**: Capital budgeting discounted cash flow analysis at $10.5\%$ WACC over a 10-year project lifetime, calculating NPV, IRR, LCOE, and break-even tonnages.
- **Cradle-to-Grave Life Cycle Assessment (LCA)**: ISO 14040/14044 compliant greenhouse gas accounting with IPCC AR6 GWP100 metrics ($\text{CH}_4=27.90, \text{N}_2\text{O}=273.00$), thermal coal displacement ($0.98\text{ t }\text{CO}_2\text{e}/\text{t}$), 100-year biochar recalcitrance ($2.20\text{ t }\text{CO}_2\text{e}/\text{t}$), and Verra VM0044 additionality certification.

### System C: Multi-User Experience, Security & Governance (Phases 13 & 14)
- **Role-Oriented Workspaces**: 7 distinct persona workspaces (`Public Visitor`, `Farmer`, `Field Operator`, `Agricultural Analyst`, `Environmental Analyst`, `Organization Manager`, `System Administrator`) plus `Technical Engine Explorer`.
- **Multilingual Localization**: Verified UI translations in English (`en`), Hindi (`hi`), and Punjabi (`pa`).
- **Professional Typography**: Strict zero-emoji interface adhering to professional enterprise design guidelines.
- **Cryptographic Security**: Salted PBKDF2-SHA256 password hashing (100,000 rounds), HMAC-SHA256 JWT access and refresh tokens, and active session management.
- **Granular RBAC & Tenant Isolation**: 32 distinct permissions, row-level tenant organization partitioning, and object-level ownership guards.
- **DPDP Act 2023 Technical Controls**: Purpose-bound consent recording and withdrawal, Data Subject Request (DSR) management, and 2-decimal geospatial location obfuscation (~1.1 km blur for public access). Statutory compliance requires independent legal review.
- **Immutable Audit Trails**: Relational `audit_logs` and `security_events` with database engine triggers forbidding update and delete operations.

### System D: Production Quality, DevOps & Release Readiness (Phases 15 to 17)
- **100% Automated Test Suite**: 145 automated tests across 8 categories (Unit, Integration, Regression, Scientific, Performance, Reliability, and E2E) with 100% pass rate.
- **Scientific Validation Report**: Comprehensive documentation in `docs/SCIENTIFIC_VALIDATION.md`.
- **Hardened Multi-Stage Dockerfile**: Unprivileged non-root user execution (`stubble_app`, UID 10001) with internal healthchecks.
- **Fail-Closed Production Compose**: Isolated Docker network, zero host database port exposure, and resource quotas.
- **Automated CI/CD Pipeline**: 6-stage GitHub Actions workflow covering secret scanning, linting, security scanning, testing, container build, and deployment.
- **Disaster Recovery Subsystem**: Automated database backup and restore utilities (`scripts/backup_db.py`, `scripts/restore_db.py`) with AES-128-CBC/Fernet encryption, cryptographic SHA-256 verification, confirmation-gated destruction prevention, and automated retention management.

---

## Quickstart & Local Execution

### 1. Prerequisites
- Python 3.11+
- Git
- (Optional) Docker and Docker Compose

### 2. Local Installation
```bash
# Clone the repository
git clone https://github.com/your-org/stubble2power.git
cd stubble2power

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and insert your NASA FIRMS MAP key if available
```

### 3. Initialize and Seed the Database
```bash
# Initialize schema and seed benchmark reference data
python -c "
from backend.models.entities import Base
from backend.core.database.engine import engine
from database.seeds.seed_data import seed_all
Base.metadata.create_all(bind=engine)
seed_all()
print('Database initialized and benchmark data seeded successfully.')
"
```

### 4. Run the Backend API Server
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Run the Streamlit Frontend Dashboard
```bash
streamlit run app.py --server.port=8501
```
Open your browser at `http://localhost:8501`.

---

## Production Deployment via Docker Compose

### 1. Configure Production Environment
```bash
cp .env.production.example .env.production
# Securely configure POSTGRES_PASSWORD, JWT_SECRET_KEY, and NASA_FIRMS_MAP_KEY
```

### 2. Deploy Full Stack
```bash
# Build and launch production stack with zero host DB port exposure
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# Verify container health
docker compose -f docker-compose.prod.yml ps
```

---

## Automated Testing & Scientific Verification

Execute the complete 145-test automated pyramid:

```bash
# Run all test suites
python -m pytest tests/ -v

# Run scientific validation suite specifically
python -m pytest tests/scientific/ -v

# Run end-to-end user workflows
python -m pytest tests/e2e/ -v

# Run performance benchmarks
python -m pytest tests/performance/ -v

# Run reliability & fault-tolerance tests
python -m pytest tests/reliability/ -v
```

---

## Documentation Suite

| Document | Description |
|:---|:---|
| [SCIENTIFIC_VALIDATION.md](docs/SCIENTIFIC_VALIDATION.md) | Peer-reviewed mathematical models, empirical tests, and literature benchmarks. |
| [DEPLOYMENT_ARCHITECTURE.md](docs/DEPLOYMENT_ARCHITECTURE.md) | System topology, container network isolation, resource limits, and security perimeter. |
| [DEPLOYMENT_RUNBOOK.md](docs/DEPLOYMENT_RUNBOOK.md) | Production setup, TLS/Nginx reverse proxy, rolling updates, and disaster recovery. |
| [USER_GUIDES.md](docs/USER_GUIDES.md) | Step-by-step operating manuals for Farmers, Fleet Operators, Plant Managers, Analysts, and Admins. |
| [API.md](docs/API.md) | OpenAPI REST API route catalog covering all 21 router groups. |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Centralized configuration registry catalog (85+ parameters with provenance metadata). |
| [SECURITY_THREAT_MODEL.md](docs/SECURITY_THREAT_MODEL.md) | STRIDE threat model, mitigation strategies, and attack surface analysis. |
| [PRIVACY_GOVERNANCE.md](docs/PRIVACY_GOVERNANCE.md) | DPDP Act 2023 compliance, purpose-bound consent, and DSR handling. |
| [OPERATIONAL_HANDOVER.md](docs/OPERATIONAL_HANDOVER.md) | Production SLA, incident response escalation, monitoring metrics, and maintenance schedules. |
| [RELEASE_NOTES_v2.5.0.md](docs/RELEASE_NOTES_v2.5.0.md) | Certified release notes for v2.5.0 closing Phases 0 through 17. |
| [THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md) | Open-source licensing attributions and citations (NASA FIRMS, OSM, PostGIS). |

---

## Non-Negotiable Architectural Principles

1. **Zero Hardcoding**: All agricultural, economic, geographic, logistical, and technical parameters reside in the centralized `ConfigManager` registry with literature citations and bounds.
2. **Zero Fake Results**: Every test result, benchmark, and empirical validation reported is generated through real code execution against standard datasets.
3. **Zero Fake Deployment**: Multi-stage container builds, non-root user execution, and secure compose files are tested and functional.
4. **Preserve Existing Functionality**: All features from Phase 0 to Phase 14 remain fully operational and verified.
5. **Scientific Correctness**: Formulations strictly adhere to NASA remote sensing standards, PAU agronomy, NRIDA road networks, DCF capital budgeting, and IPCC AR6 LCA guidelines.
6. **Security by Default**: Non-root container execution, fail-closed production settings, salted PBKDF2 hashing, immutable audit logs, and purpose-bound consent filtering.
7. **Clean Professional Typography**: No decorative emojis across all production user interfaces and documentation.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
All NASA satellite data products are subject to the NASA Open Data Policy.
