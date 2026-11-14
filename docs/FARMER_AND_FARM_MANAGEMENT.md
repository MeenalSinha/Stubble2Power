# Farmer & Farm Management Architecture
## Phase 10: Agricultural Intelligence Specification

---

## 1. Overview & Purpose

The **Farmer & Farm Management** module bridges satellite Earth observation with on-the-ground agricultural reality. In Indian agriculture, particularly across Punjab and Haryana, a single enrolled farmer often operates multiple non-contiguous parcels across different villages and tehsils. Furthermore, agricultural land ownership patterns (owner-cultivator vs. cash tenant) significantly influence residue management choices.

This module introduces spatial parcel-level modeling (`Farm`), crop cultivation records (`FarmCrop`), and measured harvest events (`HarvestRecord`) tied to enrolled farmers (`Farmer`) while upholding strict data privacy standards.

---

## 2. Entity Relational Architecture

```
  +------------------+         1 : N         +--------------------+
  |      Farmer      | --------------------> |        Farm        |
  |  id (PK)         |                       |  id (PK)           |
  |  name            |                       |  farmer_id (FK)    |
  |  phone_masked    |                       |  farm_name         |
  |  consent_given   |                       |  total_acres       |
  |  district        |                       |  latitude/longitude|
  |  verification    |                       |  soil_type         |
  +------------------+                       |  boundary_geojson  |
                                             +--------------------+
                                                       | 1 : N
                                                       v
                                             +--------------------+
                                             |      FarmCrop      |
                                             |  id (PK)           |
                                             |  farm_id (FK)      |
                                             |  crop_type         |
                                             |  cultivated_acres  |
                                             |  crop_season       |
                                             |  crop_year         |
                                             |  sowing_date       |
                                             |  status            |
                                             +--------------------+
                                                       | 1 : N
                                                       v
                                             +--------------------+
                                             |   HarvestRecord    |
                                             |  id (PK)           |
                                             |  farm_crop_id (FK) |
                                             |  harvest_date      |
                                             |  actual_grain_yield|
                                             |  grain_moisture_pct|
                                             |  harvest_method    |
                                             |  is_measured       |
                                             +--------------------+
```

---

## 3. Spatial Boundary and Centroid Modeling

Each `Farm` record supports both precise geodesic point coordinates (latitude, longitude) and optional polygon spatial boundaries (`boundary_geojson`).
- **Coordinate Validation:** Centroids are validated using `GeospatialService.validate_coordinates`, enforcing strict bounds ($[-90, +90]$ latitude, $[-180, +180]$ longitude) and checking against known agricultural districts in Punjab (e.g., Ludhiana, Sangrur, Patiala, Bathinda, Firozpur, Amritsar).
- **Acreage Conservation Guard:** Cultivated acres across active crops on a farm parcel are strictly bounded:
  $$\sum \text{cultivated\_acres} \le \text{farm.total\_acres}$$
  Any attempt to register crop acreage exceeding total parcel acreage raises a `ValidationError`.

---

## 4. Farmer Privacy Safeguards

In compliance with India's Digital Personal Data Protection (DPDP) Act 2023:
1. **Masked Phone Identifiers:** Plaintext phone numbers are never stored in plain view; they are masked at ingestion (`XXXXX43210`) in the database entity.
2. **Explicit Consent Flag:** Each farmer record maintains `consent_given: bool` verifying that the farmer consented to share farm parcel coordinates for mobile residue collection.
3. **Audit Tracking:** All state transitions and spatial edits record timestamps and verification statuses (`VERIFIED`, `PENDING_SURVEY`, `REJECTED`).

---

## 5. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/farms/` | Registers a new farm parcel under an enrolled farmer |
| `GET` | `/api/farms/` | Lists registered farm parcels with district, state, and soil filters |
| `GET` | `/api/farms/{id}` | Retrieves parcel details, acreage, and centroid coordinates |
| `POST` | `/api/farms/{id}/crops` | Records a seasonal crop cultivation cycle |
| `GET` | `/api/farms/{id}/crops` | Lists all cultivation cycles for a parcel |
| `POST` | `/api/farms/crops/{crop_id}/harvest` | Logs an empirical grain harvest yield event |
