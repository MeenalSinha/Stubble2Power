# Agricultural Fire Context Intelligence Architecture

## 1. Overview & Non-Negotiable Principle

### The Core Boundary Rule
**A satellite thermal hotspot alone must never be automatically treated as confirmed agricultural residue burning.**
Moreover:
**Unusual fire activity does NOT imply agricultural fire activity.**

Thermal anomalies observed by MODIS and VIIRS can originate from diverse sources:
- Forest and brush wildfires
- Municipal waste dump combustion
- Industrial steel/chemical flares
- Roadside scrub burning

Phase 9 implements an evidence-based attribution framework connecting satellite observations to authoritative agricultural crop calendars, Land Use Land Cover (LULC) maps, and thermal combustion physics.

---

## 2. Multi-Source Bayesian Evidence Synthesis

The context classification engine synthesizes three independent spatial, temporal, and physical evidence streams:

```
+-------------------------------------------------------------------------------+
|                       Satellite Fire Observation                              |
|                       (Latitude, Longitude, Date, FRP)                        |
+-------------------------------------------------------------------------------+
           |                                   |                              |
           v                                   v                              v
+-----------------------+           +----------------------+       +--------------------+
| 1. Spatial LULC       |           | 2. Temporal Crop     |       | 3. Thermal Physics |
|    Classification     |           |    Calendar          |       |    Verification    |
| (ESA WorldCover/NRSC) |           | (ICAR/PAU Advisory)  |       | (FRP <= 250 MW)    |
+-----------------------+           +----------------------+       +--------------------+
           \                                   |                              /
            \                                  |                             /
             v                                 v                            v
    +-------------------------------------------------------------------------------+
    |                   Bayesian Evidence Synthesis & Confidence                     |
    |                   Score = 0.45*LULC + 0.40*Calendar + 0.15*Thermal            |
    +-------------------------------------------------------------------------------+
                                           |
                                           v
    +-------------------------------------------------------------------------------+
    |                          Context Classification                               |
    |  - LIKELY_AGRICULTURAL_CONTEXT (Conf >= 0.70, Cropland + Harvest Window)     |
    |  - POSSIBLE_AGRICULTURAL_CONTEXT (Conf 0.40 - 0.69, Buffer / Extended)        |
    |  - OTHER_LAND_USE_CONTEXT (Forest / Industrial / High FRP > 250 MW)           |
    |  - UNKNOWN_OR_INSUFFICIENT_EVIDENCE (Low Confidence / Missing Data)          |
    +-------------------------------------------------------------------------------+
```

---

## 3. Authoritative Reference Datasets

### 3.1 Official Crop Calendars (ICAR / PAU)
Official agronomic calendars from Punjab Agricultural University (PAU) and the Indian Council of Agricultural Research:
- **Paddy / Rice (Kharif)**:
  - Sowing: Jun 15 – Jul 15
  - Harvest: Oct 01 – Nov 30
  - **Peak Burn Window: Oct 15 – Nov 20** (High Susceptibility)
- **Wheat (Rabi)**:
  - Sowing: Nov 01 – Dec 15
  - Harvest: Apr 10 – May 25
  - **Peak Burn Window: Apr 20 – May 15** (Medium Susceptibility)
- **Cotton (Kharif)**:
  - Sowing: Apr 15 – May 20
  - Harvest: Oct 15 – Dec 15
  - **Peak Burn Window: Nov 01 – Dec 05** (Low Susceptibility)
- **Sugarcane (Perennial)**:
  - Harvest & Trash Burning: Dec 01 – Feb 15 (Medium Susceptibility)

### 3.2 LULC Geographic Reference Zones
Georeferenced spatial boundaries distinguishing agricultural basins from sensitive non-agricultural biomes:
- `Punjab Central Agri Basin` (Ludhiana-Sangrur-Patiala): Cropland (Confidence: 0.95)
- `Punjab Western Agri Basin` (Bhatinda-Moga-Firozpur): Cropland (Confidence: 0.94)
- `Punjab Majha Agri Basin` (Amritsar-Gurdaspur): Cropland (Confidence: 0.93)
- `Shivalik Forest Reserve Belt` (Rupnagar-Hoshiarpur): Forest (Confidence: 0.92)
- `Harike Pattan Wetland Reserve` (Tarn Taran): Wetland/Water (Confidence: 0.96)
- `Ludhiana Metropolitan & Industrial Focal Point`: Urban/Industrial (Confidence: 0.93)

---

## 4. REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/agriculture/calendars` | `GET` | Retrieves active crop calendars and harvest schedules. |
| `/api/agriculture/calendars` | `POST` | Registers an official crop calendar. |
| `/api/agriculture/assessments` | `GET` | Lists agricultural context classifications with filter options. |
| `/api/agriculture/classify` | `POST` | Executes evidence-based classification across fire observations. |
| `/api/agriculture/summary` | `GET` | Returns aggregated metrics, crop breakdowns, and context ratios. |
