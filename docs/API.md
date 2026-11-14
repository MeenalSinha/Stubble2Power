# Stubble2Power - REST API Documentation

The Stubble2Power backend exposes an OpenAPI 3.0 compliant REST API implemented with FastAPI.
When running the backend server (`uvicorn backend.main:app`), interactive documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 1. System & Health Endpoints

### `GET /api/health/`
Checks database connectivity and NASA FIRMS credentials status.
- **Response**:
```json
{
  "status": "healthy",
  "app_name": "Stubble2Power",
  "environment": "development",
  "database_connected": true,
  "nasa_firms_configured": true,
  "api_version": "2.0.0"
}
```

---

## 2. Configuration Registry Endpoints

### `GET /api/config/`
Returns all active domain, economic, and scientific parameters with provenance metadata.

### `GET /api/config/{param_name}`
Returns metadata and active value for a specific parameter.

---

## 3. Agricultural & Farmer Management Endpoints

### `POST /api/farmers/`
Registers a new farmer with cultivated acreage, stubble estimate, and coordinates.
- **Request Body**:
```json
{
  "name": "Gurdev Singh",
  "village": "Khanna",
  "district": "Ludhiana",
  "acres": 15.0,
  "stubble_tons": 12.0,
  "harvest_date": "2025-10-25",
  "latitude": 30.7056,
  "longitude": 76.2222
}
```

### `GET /api/farmers/`
Lists enrolled farmers with optional query parameters (`district`, `village`, `min_stubble`).

### `GET /api/farmers/stats`
Returns aggregated count, total stubble tonnage, total acreage, and village count.

### `POST /api/farmers/import-csv`
Uploads a CSV file of farmer records for bulk ingestion.

---

## 4. Logistics & Clustering Endpoints

### `POST /api/clustering/run`
Executes geodesic K-Means clustering across enrolled farmers.
- **Query Parameters**:
  - `n_clusters` (default: 4)
  - `scenario` (default: "Base Case")
- **Response**: `ClusteringResult` schema with cluster metrics, mobile transit costs, and assigned points.

---

## 5. Economics & Environmental Simulation Endpoints

### `GET /api/economics/calculate`
Calculates unit economics, production yields, revenues, costs, margins, and breakeven tonnage.
- **Parameters**: `stubble_tons`, `transport_cost`, `scenario`.

### `GET /api/economics/logistics-savings`
Calculates cost reduction of mobile refineries vs centralized processing plants.
- **Parameters**: `mobile_cost`, `stubble_tons`.

### `GET /api/economics/environmental-impact`
Returns avoided CO2, thermal coal replacement, and EPA social equivalents.
- **Parameters**: `stubble_tons`, `scenario`.

---

## 6. NASA Earth Observation Endpoints

### `GET /api/nasa/status`
Returns NASA FIRMS API status, supported satellite products, and database observation counts.

### `POST /api/nasa/ingest/country`
Triggers an ingestion job for a country (e.g. `IND`) from NASA FIRMS.
- **Query Parameters**: `country_code`, `source`, `day_range`, `date_str`.

---

## 7. Harmonization & Activity Calendar Endpoints

### `POST /api/harmonization/run`
Executes the scientific cross-sensor harmonization engine.
- **Query Parameters**: `name`, `date_start`, `date_end`, `grid_resolution_deg`.

### `GET /api/harmonization/latest`
Returns metadata of the most recent harmonization execution.

### `GET /api/calendar/daily`
Derives continuous daily activity calendar entries from harmonized database records.
- **Parameters**: `date_start`, `date_end`.

### `GET /api/calendar/monthly`
Returns monthly aggregations and burning patterns for a given year.
- **Parameters**: `year` (e.g. 2025).

### `GET /api/calendar/annual`
Returns annual burning summaries and detected peak burning dates.
- **Parameters**: `year`.

---

## 8. Seasonal & Anomaly Intelligence Endpoints

### `GET /api/seasonal/profiles`
Returns seasonal fire activity profiles (onset, peak, decay, duration, profile curve).

### `GET /api/seasonal/baselines`
Returns historical parametric ($\mu, \sigma$) and robust ($\text{Median}, \text{MAD}$) baselines.

### `GET /api/anomalies`
Returns detected statistical fire anomalies with severity levels and JSON diagnostic rationales.

---

## 9. Agricultural Fire Context Intelligence Endpoints

### `GET /api/agriculture/calendars`
Returns official state and district crop calendars.

### `GET /api/agriculture/assessments`
Returns Bayesian agricultural context assessments for satellite observations.

### `POST /api/agriculture/classify`
Triggers evidence synthesis context classification across temporal, spatial LULC, and thermal domains.

---

## 10. Farm & Cultivation Intelligence Endpoints

### `POST /api/farms/`
Registers a new agricultural farm parcel linked to an enrolled farmer.

### `GET /api/farms/`
Lists registered farm parcels with optional district, state, and soil type filtering.

### `GET /api/farms/{farm_id}`
Retrieves farm details, acreage, and centroid coordinates.

### `POST /api/farms/{farm_id}/crops`
Registers a seasonal crop cultivation cycle on a parcel.

### `GET /api/farms/{farm_id}/crops`
Lists all cultivation cycles for a specific farm parcel.

### `POST /api/farms/crops/{crop_id}/harvest`
Records an empirical grain harvest yield event and moisture content.

---

## 11. Biomass Estimation & Inventory Endpoints

### `POST /api/biomass/estimate`
Calculates net usable crop residue with crop-specific RPR, 25% soil retention, fodder deduction, and handling losses.

### `GET /api/biomass/estimates/{estimate_id}`
Retrieves a specific biomass estimate record.

### `GET /api/biomass/estimates/crop/{crop_id}`
Lists biomass estimates for a crop cultivation cycle.

### `POST /api/biomass/inventory/transaction`
Transitions biomass through audited lifecycle stages (`COMMITTED`, `ALLOCATED`, `PROCESSED`) with double-allocation guard.

### `GET /api/biomass/summary`
Returns aggregate regional biomass availability, commitments, and allocations.

---

## 12. Mobile Bio-Refinery Fleet & Deployment Endpoints

### `POST /api/mobile-units/`
Registers a trailer-mounted densification or pyrolysis unit in the active fleet.

### `GET /api/mobile-units/`
Lists mobile bio-refineries with optional status and technology filters.

### `GET /api/mobile-units/{unit_id}`
Retrieves operational specifications and depot location for a unit.

### `PATCH /api/mobile-units/{unit_id}/status`
Updates unit operational status (`AVAILABLE`, `DEPLOYED`, `MAINTENANCE`).

### `POST /api/deployments/plan`
Generates a multi-unit capacity-constrained deployment plan with road network routing.

### `GET /api/deployments/`
Lists existing deployment plans with utilization metrics.

### `GET /api/deployments/{plan_id}`
Retrieves deployment plan details, farm assignments, and unserved farm audits.

### `GET /api/deployments/{plan_id}/routes`
Retrieves vehicle route plans with sequenced stops, road distance (1.35x tortuosity), duration, and fuel consumption.

---

## 13. Advanced Techno-Economics Endpoints

### `POST /api/economics/scenario`
Evaluates CAPEX, OPEX, farmer incentive payments, product revenues (briquettes + biochar), break-even tonnage, ROI, payback, NPV, and IRR.

### `GET /api/economics/scenarios`
Lists evaluated financial scenarios.

### `GET /api/economics/compare`
Runs Conservative, Base Case, and Optimistic models side-by-side.

### `GET /api/economics/scenarios/{id}/sensitivity`
Generates sensitivity tornado factors across briquette price, biochar price, farmer payout, and retail diesel price.

---

## 14. Life Cycle Assessment (LCA) Endpoints

### `POST /api/environmental/lca`
Computes cradle-to-grave net GHG benefits (baseline burning vs project diesel vs coal displacement vs biochar sequestration).

### `GET /api/environmental/assessments`
Lists completed life cycle assessments.

### `GET /api/environmental/system-boundary`
Returns official LCA system boundary, IPCC AR6 GWP metrics, and CEA India emissions factor provenance.
