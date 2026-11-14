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

### 3.7 `farms` (Phase 10)
Spatially bounded farm parcels belonging to enrolled farmers.
- `id` (INTEGER, PK)
- `farmer_id` (FK -> `farmers.id`)
- `farm_name` (VARCHAR(150))
- `total_acres` (FLOAT)
- `village`, `district`, `state` (VARCHAR(150))
- `latitude`, `longitude` (FLOAT, Indexed)
- `ownership_status`, `soil_type`, `verification_status` (VARCHAR(50))
- `boundary_geojson` (JSON, Optional)

### 3.8 `farm_crops` (Phase 10)
Seasonal cultivation cycles on a farm parcel.
- `id` (INTEGER, PK)
- `farm_id` (FK -> `farms.id`)
- `crop_type` (VARCHAR(50), e.g. PADDY, WHEAT)
- `cultivated_acres` (FLOAT)
- `crop_season`, `crop_year` (VARCHAR/INTEGER)
- `sowing_date`, `expected_harvest_date`, `actual_harvest_date` (DATE)
- `expected_yield_tons_per_acre`, `actual_yield_tons_per_acre` (FLOAT)
- `cultivation_status` (VARCHAR(50))

### 3.9 `harvest_records` (Phase 10)
Empirical measured harvest events.
- `id` (INTEGER, PK)
- `farm_crop_id` (FK -> `farm_crops.id`)
- `harvest_date` (DATE)
- `actual_grain_yield_tons` (FLOAT)
- `grain_moisture_pct` (FLOAT)
- `harvest_method` (VARCHAR(50))
- `is_measured` (BOOLEAN)

### 3.10 `biomass_estimates` (Phase 10)
Mathematical residue deductions and net usable biomass.
- `id` (INTEGER, PK)
- `farm_crop_id` (FK -> `farm_crops.id`)
- `gross_residue_tons`, `retained_residue_tons`, `competing_demand_tons` (FLOAT)
- `collectable_residue_tons`, `handling_loss_tons`, `net_usable_biomass_tons` (FLOAT)
- `dry_matter_tons`, `moisture_content_pct` (FLOAT)
- `estimation_source` (VARCHAR(50))
- `confidence_score` (FLOAT)
- `availability_start_date`, `availability_end_date` (DATE)

### 3.11 `biomass_inventory_transactions` (Phase 10)
Audited lifecycle ledger transitions.
- `id` (INTEGER, PK)
- `biomass_estimate_id` (FK -> `biomass_estimates.id`)
- `farm_id` (FK -> `farms.id`)
- `quantity_tons` (FLOAT)
- `stage` (VARCHAR(50): ESTIMATED, CONFIRMED, COMMITTED, COLLECTED, STORED, ALLOCATED, PROCESSED)
- `allocated_unit_id` (INTEGER, Optional)
- `transaction_timestamp` (DATETIME)

### 3.12 `mobile_bio_refineries` (Phase 11)
Fleet specifications and home depot registry.
- `id` (INTEGER, PK)
- `unit_code` (VARCHAR(50), Unique Index)
- `name` (VARCHAR(150))
- `technology` (VARCHAR(50): BRIQUETTING, SLOW_PYROLYSIS)
- `hourly_capacity_tons`, `daily_operating_hours`, `daily_capacity_tons` (FLOAT)
- `fuel_consumption_liters_per_ton`, `operating_cost_per_hour_inr` (FLOAT)
- `home_depot_name` (VARCHAR(150))
- `home_latitude`, `home_longitude` (FLOAT)
- `max_travel_radius_km` (FLOAT)
- `current_status` (VARCHAR(50))

### 3.13 `deployment_plans` & `deployment_assignments` (Phase 11)
Capacity-constrained multi-unit operational deployments.
- `deployment_plans`: `plan_code`, `date_start`, `date_end`, `status`, `total_biomass_assigned_tons`, `total_units_deployed`, `total_route_distance_km`, `estimated_transport_cost_inr`, `unserved_farms_count`, `capacity_utilization_pct`, `parameters_json`.
- `deployment_assignments`: `deployment_plan_id`, `mobile_unit_id`, `farm_id`, `assigned_biomass_tons`, `scheduled_date`, `collection_status`.

### 3.14 `route_plans` (Phase 11)
Sequenced vehicle collection stops with road tortuosity modeling.
- `id` (INTEGER, PK)
- `deployment_plan_id` (FK -> `deployment_plans.id`)
- `mobile_unit_id` (FK -> `mobile_bio_refineries.id`)
- `total_distance_km`, `road_tortuosity_ratio` (FLOAT)
- `estimated_duration_hours`, `fuel_consumed_liters`, `total_payload_tons` (FLOAT)
- `stops_json` (JSON list of sequenced stops: DEPOT_START, FARM_COLLECTION, DEPOT_END)

### 3.15 `financial_scenarios` (Phase 12)
Techno-economic capital budgeting evaluations.
- `id` (INTEGER, PK)
- `deployment_plan_id` (FK -> `deployment_plans.id`, Optional)
- `scenario_name` (VARCHAR(50))
- `briquette_price_per_ton`, `biochar_price_per_ton`, `farmer_procurement_price_per_ton`, `diesel_price_per_liter` (FLOAT)
- `total_biomass_processed_tons`, `total_revenue_inr`, `total_opex_inr`, `gross_profit_inr`, `net_margin_pct` (FLOAT)
- `break_even_tons`, `roi_pct`, `payback_period_years`, `npv_inr`, `irr_pct` (FLOAT)

### 3.16 `environmental_assessments` (Phase 12)
Cradle-to-grave life cycle assessments.
- `id` (INTEGER, PK)
- `biomass_diverted_tons` (FLOAT)
- `baseline_total_co2e_tons`, `project_total_emissions_co2e_tons` (FLOAT)
- `coal_displaced_tons`, `avoided_coal_co2e_tons` (FLOAT)
- `biochar_stable_carbon_stored_co2e_tons` (FLOAT)
- `net_avoided_co2e_tons`, `net_benefit_ratio` (FLOAT)
- `carbon_credit_eligible_tons` (FLOAT)
- `methodology_provenance` (VARCHAR(255))

---

## 4. Migrations & Seed Management
- Alembic configuration resides in `alembic.ini` and `database/migrations/`.
- Seed data for administrative regions, benchmark farmers, and satellite fire observations is executed via `python database/seeds/seed_data.py`.
