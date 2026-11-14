# Stubble2Power - Phase 0 Comprehensive Audit & Technical Debt Report

## 1. Executive Summary

A comprehensive forensic audit of the legacy Stubble2Power codebase (`app.py`, 1,679 lines) was conducted. The application is an early-stage prototype demonstrating a simulation of mobile bio-refineries in Punjab, India. While the visual UI concept was established using Streamlit and Glassmorphism CSS, the system suffered from monolithic architecture, tight coupling between UI and business calculations, multiple critical UI logic bugs, complete session-state fragility, zero database persistence, and extensive hardcoding of domain, geospatial, and economic variables.

This audit establishes the baseline for transforming the prototype into an enterprise-ready, NASA-powered agricultural fire intelligence and mobile bio-refinery optimization platform.

---

## 2. Legacy Functionality Verification Checklist

| Section | Feature | Verification Status | Defect / Limitation Found |
|---|---|---|---|
| **A. Home** | Overview, problem statement, solution | Verified | Glassmorphism cards and metrics render correctly. No real data link; purely static copy. |
| **A. Home** | Quick Start Demo | Verified | Streamlit button sets session state and launches balloons. |
| **B. Data Input** | Manual Farmer Registration | Verified with bugs | Random offset `±0.05` applied to village coordinates. No database persistence; all data lost on refresh. |
| **B. Data Input** | Quick Action: 20 Sample Farmers | Verified | Generates random data in session state using hardcoded village list. Violates non-negotiable rule on synthetic records. |
| **B. Data Input** | Data Table & CSV Export | Verified | Exports Pandas dataframe to CSV. |
| **C. Clustering** | K-Means Grouping | Verified with bugs | Hardcoded default `n_clusters=4`. If farmer data is empty, executes `return` which prematurely truncates page render. |
| **C. Clustering** | Route distance calculation | Verified with defects | Uses flat Euclidean approximation `np.sqrt(dx^2 + dy^2) * 111` instead of Haversine or geodesic metrics. |
| **C. Clustering** | Transport Cost & Folium Map | Verified with defects | Hardcoded map center `[30.7333, 76.7794]` (Chandigarh). |
| **D. Economics** | 3 Scenarios (Conservative, Base, Optimistic) | Verified | Calculates production, revenue, cost, margins, breakeven. |
| **D. Economics** | Financial charts & tables | Verified | Plotly pie charts and summary tables function. |
| **E. Dashboard** | Executive summary KPIs | Verified with bugs | If data not populated, executes `return` aborting subsequent tabs and footer. |
| **E. Dashboard** | Operations & Impact panels | Verified with bugs | Redundant Plotly call in `else` branch of margin indicator (syntax/logic anomaly). |

---

## 3. Critical Bugs & Technical Debt Identified

### Defect 0.1: Early `return` in Streamlit Tab Blocks
In `app.py` lines 711, 893, and 1192:
```python
if st.session_state.farmer_data.empty:
    st.markdown("...")
    return
```
Calling `return` inside a Streamlit tab function immediately aborts the enclosing `main()` function, preventing subsequent tabs and the application footer from rendering.
**Fix**: Replace early returns with conditional tab-scoped empty-state containers.

### Defect 0.2: Redundant Code and Scope Leak in Dashboard Tab
In `app.py` line 1648-1649:
```python
color_discrete_sequence=['#f44336', '#ff9800', '#ffc107']
st.plotly_chart(fig_cost, use_container_width=True)
```
In the `else:` branch of the final profitability status indicator, `color_discrete_sequence` is assigned without effect and `fig_cost` from earlier in the page is re-rendered inappropriately.
**Fix**: Remove the dangling statement and redundant chart re-draw.

### Defect 0.3: Inaccurate Geospatial Distance Calculation
In `app.py` lines 764-765:
```python
dist = np.sqrt((coords_cluster[i][0] - coords_cluster[j][0])**2 + 
               (coords_cluster[i][1] - coords_cluster[j][1])**2) * 111
```
Multiplying latitude/longitude degree Euclidean distance by 111 km produces substantial distortion (up to 20-30% error in longitude scaling at latitude 30°N where 1 degree of longitude is ~96.5 km).
**Fix**: Migrate to great-circle Haversine formula and PostGIS `ST_Distance` / `ST_DistanceSphere`.

### Defect 0.4: Magic Numbers in Logistics Savings
In `app.py` line 400:
```python
central_cost = stubble_tons * 100 * 150 / 10
```
Values `100` (assumed km to central plant), `150` (transport cost per km), and `10` (truck capacity tons) are hardcoded inline without documentation or configuration.
**Fix**: Externalize all logistic parameters to the configuration registry with documented units and validation rules.

### Defect 0.5: Lack of Clean Module Importability
In `app.py`, top-level module code immediately calls Streamlit runtime routines (`st.set_page_config`, `st.markdown`, `st.session_state`). When imported by unit tests or external microservices, warnings and state errors occur.
**Fix**: Decouple business logic into pure Python services in `backend/` completely independent of Streamlit.

---

## 4. Hardcoding Audit & Migration Register

The following parameters were identified as hardcoded in `app.py` and must be migrated to the database/config architecture:

| Category | Hardcoded Item | Legacy Value in `app.py` | Target Config / Table |
|---|---|---|---|
| **Geography** | Default Map Center | `[30.7333, 76.7794]` (Chandigarh) | `areas_of_interest.center_coordinates` / `config_registry` |
| **Geography** | Sample Village Registry | 15 Punjab cities with fixed lat/lon | `administrative_regions` & `villages` database tables |
| **Geography** | Coordinate Jitter | `random.uniform(-0.05, 0.05)` | Deprecate synthetic jitter; use validated spatial inputs |
| **Economics** | Scenario: Conservative | Yields (0.6, 0.15), Prices (5, 12), Payment (1200) | `economic_scenarios` & `config_registry` |
| **Economics** | Scenario: Base Case | Yields (0.7, 0.2), Prices (6, 15), Payment (1500) | `economic_scenarios` & `config_registry` |
| **Economics** | Scenario: Optimistic | Yields (0.75, 0.22), Prices (7, 18), Payment (1800) | `economic_scenarios` & `config_registry` |
| **Economics** | Carbon credit price | ₹400, ₹500, ₹600 per ton | `config_registry` (unit: INR/tCO2e) |
| **Economics** | Mobile unit transport cost | ₹180, ₹150, ₹120 per km | `config_registry` (unit: INR/km) |
| **Logistics** | Central haulage distance | 100 km | `config_registry` (`central_haulage_distance_km`) |
| **Logistics** | Central haulage cost | 150 INR/km | `config_registry` (`central_transport_rate_inr_km`) |
| **Logistics** | Central truck capacity | 10 tons | `config_registry` (`central_truck_capacity_tons`) |
| **Environmental**| CO2 avoided factor | 1.2, 1.5, 1.8 tCO2/t stubble | `config_registry` (`co2_avoided_per_ton_stubble`) |
| **Environmental**| Coal replacement ratio | 0.6, 0.8, 0.9 t coal/t stubble | `config_registry` (`coal_replaced_ratio`) |
| **Environmental**| Tree equivalent multiplier| 33 trees / tCO2 | `config_registry` (`tree_equivalent_factor`) |
| **Environmental**| Car equivalent multiplier | 0.22 cars / tCO2 | `config_registry` (`car_equivalent_factor`) |
| **Environmental**| Homes powered multiplier | 2 homes / t coal | `config_registry` (`homes_powered_factor`) |
| **Clustering** | Default cluster count | 4 | `config_registry` (`default_cluster_count`) |
| **Clustering** | Coordinate distance metric| Euclidean * 111 | `GeospatialService.haversine_distance` |

---

## 5. Architectural Blueprints

```
Legacy Monolith:
app.py (1,679 lines)
├── Streamlit Page Config & Styles
├── Hardcoded Scenarios & Villages
├── Inline Math (calculate_unit_economics, etc.)
└── UI Render Blocks with Session-State Storage

Target Modular Architecture:
Stubble2Power/
├── backend/
│   ├── api/routes/ (FastAPI endpoints: health, farmers, fire, nasa, harmonization, calendar)
│   ├── core/config/ (Typed Settings, Config Registry, Security)
│   ├── models/ (SQLAlchemy ORM + PostGIS)
│   ├── schemas/ (Pydantic validation schemas)
│   ├── repositories/ (Database abstraction layer)
│   └── services/
│       ├── farmers/ (CRUD, Validation, CSV import/export)
│       ├── clustering/ (Haversine distance, K-Means, route optimization)
│       ├── economics/ (Scenario simulation, breakeven, unit metrics)
│       ├── environmental/ (Emission factors, carbon metrics)
│       ├── nasa/ (NASA FIRMS API Client, ingestion jobs, retry, backoff)
│       ├── fire/ (Data quality control, normalization, deduplication)
│       ├── harmonization/ (Scientific MODIS-VIIRS cross-sensor association, gridding, calibration)
│       ├── calendar/ (Dynamic temporal aggregations: daily, weekly, monthly, annual)
│       └── geospatial/ (Spatial indexing, bounding box filters, GeoJSON formatting)
├── frontend/streamlit_app/ (Clean modular Streamlit interface with dedicated pages and UI components)
├── database/ (Alembic migrations, seeds, initialization)
├── tests/ (unit, integration, regression, fixtures)
└── docs/ (Full technical, scientific, and user documentation)
```

## 6. Baseline Verification Signoff
- 10 baseline regression tests created and passing (100% pass rate).
- Legacy unit economics, environmental calculations, logistics formulas, and clustering behavior verified and captured in executable regression test suite.
- Phase 0 completion criteria satisfied.
