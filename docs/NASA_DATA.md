# Stubble2Power - NASA FIRMS Satellite Data Integration

## 1. Overview & Data Sources

Stubble2Power directly addresses **NASA Space Apps Challenge 09: Harmonization of MODIS and VIIRS Hot Spots** by ingesting, normalizing, and harmonizing active fire observations from NASA's Fire Information for Resource Management System (FIRMS).

Official NASA Sources:
- NASA FIRMS Portal: https://firms.modaps.eosdis.nasa.gov/
- NASA FIRMS API Documentation: https://firms.modaps.eosdis.nasa.gov/api/
- NASA Earthdata FIRMS MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key/

---

## 2. Supported Satellite Sensors & Products

| Instrument | Satellite Platform | FIRMS Product Identifier | Nominal Resolution | Overpass Local Equator Crossing Time | Detection Characteristics |
|---|---|---|---|---|---|
| **MODIS** | Terra | `MODIS_NRT`, `MODIS_SP` | 1,000 m nadir (up to 4.8 km scan edge) | ~10:30 AM (descending) / ~10:30 PM (ascending) | Established 24+ year baseline. Detects flaming fires > 100-200 m². |
| **MODIS** | Aqua | `MODIS_NRT`, `MODIS_SP` | 1,000 m nadir (up to 4.8 km scan edge) | ~1:30 PM (ascending) / ~1:30 AM (descending) | Afternoon peak active burning alignment in Punjab agricultural season. |
| **VIIRS** | NOAA-20 (JPSS-1) | `VIIRS_NOAA20_NRT` | 375 m (I-band I4/I5) | ~1:30 PM (ascending) / ~1:30 AM (descending) | Pixel trimming restricts scan edge growth. Detects small agricultural fires (~10-20 m²). |
| **VIIRS** | Suomi-NPP | `VIIRS_SNPP_NRT` | 375 m (I-band I4/I5) | ~1:30 PM (ascending) / ~1:30 AM (descending) | Precursor to NOAA-20; coincident orbit with 50-minute offset. |
| **VIIRS** | NOAA-21 (JPSS-2) | `VIIRS_NOAA21_NRT` | 375 m (I-band I4/I5) | ~1:30 PM (ascending) / ~1:30 AM (descending) | Operational since 2023; supplements afternoon global fire coverage. |

---

## 3. API Integration Endpoints & Protocol

Stubble2Power communicates with the FIRMS REST API via the following endpoints:

### 3.1 Country Observation Stream
```http
GET https://firms.modaps.eosdis.nasa.gov/api/country/csv/[MAP_KEY]/[SOURCE]/[COUNTRY]/[DAY_RANGE]/[DATE]
```
- Parameters:
  - `[MAP_KEY]`: 32-character FIRMS authentication key.
  - `[SOURCE]`: `MODIS_NRT`, `VIIRS_NOAA20_NRT`, etc.
  - `[COUNTRY]`: 3-letter ISO 3166-1 country code (e.g. `IND` for India).
  - `[DAY_RANGE]`: 1 to 10 days.
  - `[DATE]`: Optional `YYYY-MM-DD` historical anchor date.

### 3.2 Area Bounding Box Stream
```http
GET https://firms.modaps.eosdis.nasa.gov/api/area/csv/[MAP_KEY]/[SOURCE]/[min_lon,min_lat,max_lon,max_lat]/[DAY_RANGE]/[DATE]
```

### 3.3 Data Availability Check
```http
GET https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/[MAP_KEY]/[SOURCE]
```

---

## 4. Quality Control & Normalization Pipeline

Raw NASA observations pass through `QualityControlService` before storage:
1. **Coordinate Validation**: Ensures latitude [-90, +90] and longitude [-180, +180].
2. **Timestamp Normalization**: Parses acquisition date and HHMM string into a standard UTC datetime.
3. **Confidence Standardization**:
   - MODIS: Percentage 0-100 mapped to float `[0.0, 1.0]`.
   - VIIRS: Categorical values `low` -> 0.3, `nominal` -> 0.7, `high` -> 1.0.
4. **Energy Validation**: Verifies positive Fire Radiative Power (FRP) and brightness temperature within physical bounds [150K, 600K].
5. **Idempotent Hashing**: Generates SHA-256 hash from `satellite|instrument|date|time|lat|lon` to prevent duplicate insertions on repeated API polls.
6. **Quarantine Management**: Rejects corrupted records with explicit audit reasons stored in `quarantine_reason`.

---

## 5. Provenance & Attribution
All satellite observation records maintain full source attribution:
- Satellite name (e.g. `Aqua`, `NOAA-20`)
- Instrument (`MODIS`, `VIIRS`)
- Original raw confidence
- Acquisition timestamp
- Ingestion job UUID
