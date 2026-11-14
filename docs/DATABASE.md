# Stubble2Power - Database Architecture & Schema Documentation

## 1. Overview

Stubble2Power uses a relational database architecture with spatial query capabilities.
- **Production**: PostgreSQL 16 with PostGIS 3.4 for advanced spatial indexing and geodesic calculations.
- **Development & Portable Testing**: SQLite 3.50+ with Python-level Shapely and Haversine geodesic calculations.

---

## 2. Entity Relationship Model

```
+-------------------+        +--------------------+
|   organizations   |------< |       users        |
+-------------------+        +--------------------+

+-------------------+
|      farmers      | (Spatially indexed latitude/longitude, village, district, state)
+-------------------+

+-------------------+        +--------------------+
|  ingestion_jobs   |------< | raw_sat_obs        | (Immutable source payload)
+-------------------+        +--------------------+
          |
          |                  +--------------------+
          +----------------< | normalized_sat_obs | (Standardized fields, grid_id, FRP, UTC)
                             +--------------------+

+-------------------+        +--------------------+
| harmonization_runs|------< |  harmonized_obs    | (Gridded cells, consensus, activity index)
+-------------------+        +--------------------+

+-------------------+
| config_parameters | (Name, value, unit, description, scientific source, version)
+-------------------+

+-------------------+
| areas_of_interest | (Name, country, bounding box)
+-------------------+
```

---

## 3. Detailed Table Specifications

### 3.1 `farmers`
Persists registered agricultural residue sources.
- `id` (INTEGER, PK)
- `name` (VARCHAR(150), Indexed)
- `village` (VARCHAR(150), Indexed)
- `district` (VARCHAR(150), Indexed)
- `state` (VARCHAR(150), Default 'Punjab')
- `country` (VARCHAR(50), Default 'IND')
- `acres` (FLOAT)
- `stubble_tons` (FLOAT)
- `harvest_date` (DATE)
- `latitude` (FLOAT, Indexed)
- `longitude` (FLOAT, Indexed)
- `created_at` (DATETIME)
- `updated_at` (DATETIME)
- *Indexes*: `(latitude, longitude)`, `(state, district, village)`.

### 3.2 `ingestion_jobs`
Lifecycle tracker for satellite ingestion requests.
- `id` (INTEGER, PK)
- `job_uuid` (VARCHAR(64), Unique, Indexed)
- `satellite` (VARCHAR(50))
- `instrument` (VARCHAR(50))
- `source_endpoint` (VARCHAR(255))
- `date_start` (DATE)
- `date_end` (DATE)
- `status` (VARCHAR(50)) - `PENDING`, `RUNNING`, `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `FAILED`
- `records_retrieved` (INTEGER)
- `records_valid` (INTEGER)
- `records_quarantined` (INTEGER)
- `error_message` (TEXT)
- `started_at` (DATETIME)
- `completed_at` (DATETIME)

### 3.3 `raw_satellite_observations`
Immutable raw observation repository preserving the original untouched API payload.
- `id` (INTEGER, PK)
- `ingestion_job_id` (FK -> `ingestion_jobs.id`)
- `record_hash` (VARCHAR(64), Unique, Indexed)
- `source_satellite` (VARCHAR(50))
- `raw_payload` (JSON)
- `retrieved_at` (DATETIME)

### 3.4 `normalized_satellite_observations`
Canonical observation layer standardized for scientific analysis.
- `id` (INTEGER, PK)
- `source_record_hash` (VARCHAR(64), Unique, Indexed)
- `ingestion_job_id` (FK -> `ingestion_jobs.id`)
- `satellite` (VARCHAR(50), Indexed)
- `instrument` (VARCHAR(50), Indexed) - `MODIS` or `VIIRS`
- `product_version` (VARCHAR(50))
- `acquisition_date` (DATE, Indexed)
- `acquisition_time_utc` (VARCHAR(10))
- `timestamp_utc` (DATETIME, Indexed)
- `latitude` (FLOAT, Indexed)
- `longitude` (FLOAT, Indexed)
- `brightness` (FLOAT) - Kelvin
- `bright_t31` (FLOAT) - Channel 31 Kelvin
- `frp` (FLOAT) - Fire Radiative Power (MW)
- `confidence_raw` (VARCHAR(50))
- `confidence_normalized` (FLOAT) - [0.0, 1.0]
- `daynight` (VARCHAR(10)) - `D` or `N`
- `scan` (FLOAT)
- `track` (FLOAT)
- `spatial_grid_id` (VARCHAR(50), Indexed)
- `is_valid` (BOOLEAN, Indexed)
- `quarantine_reason` (VARCHAR(255))
- *Indexes*: `(acquisition_date, latitude, longitude)`, `(spatial_grid_id, acquisition_date)`.

### 3.5 `harmonization_runs`
Maintains execution history, parameter provenance, and summary results for reproducibility.
- `id` (INTEGER, PK)
- `run_uuid` (VARCHAR(64), Unique, Indexed)
- `name` (VARCHAR(150))
- `date_start` (DATE)
- `date_end` (DATE)
- `grid_resolution_deg` (FLOAT)
- `total_input_observations` (INTEGER)
- `harmonized_cells_count` (INTEGER)
- `associated_pairs_count` (INTEGER)
- `mean_consensus_score` (FLOAT)
- `algorithm_version` (VARCHAR(50))
- `status` (VARCHAR(50))
- `parameters_json` (JSON)
- `created_at` (DATETIME)

### 3.6 `harmonized_observations`
Derived spatial grid cell observations combining MODIS and VIIRS records.
- `id` (INTEGER, PK)
- `harmonization_run_id` (FK -> `harmonization_runs.id`)
- `grid_id` (VARCHAR(50), Indexed)
- `observation_date` (DATE, Indexed)
- `centroid_lat` (FLOAT)
- `centroid_lon` (FLOAT)
- `modis_count` (INTEGER)
- `viirs_count` (INTEGER)
- `total_detections` (INTEGER)
- `associated_pairs_count` (INTEGER)
- `modis_mean_frp` (FLOAT)
- `viirs_mean_frp` (FLOAT)
- `harmonized_frp_mw` (FLOAT)
- `harmonized_activity_index` (FLOAT) - [0.0, 100.0]
- `consensus_score` (FLOAT) - [0.0, 1.0]
- `uncertainty_level` (VARCHAR(20)) - `LOW`, `MODERATE`, `HIGH`
- `data_coverage_flag` (VARCHAR(50)) - `DUAL_SENSOR`, `VIIRS_ONLY`, `MODIS_ONLY`, `ZERO_DETECTED`

---

## 4. Migrations & Seed Management
- Alembic configuration resides in `alembic.ini` and `database/migrations/`.
- Seed data for administrative regions, benchmark farmers, and satellite fire observations is executed via `python database/seeds/seed_data.py`.
