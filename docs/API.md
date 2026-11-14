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
