# Stubble2Power - MODIS–VIIRS Scientific Harmonization Methodology

## 1. Challenge & Problem Statement

**NASA Space Apps Challenge 09**: Harmonization of MODIS and VIIRS Hot Spots requires a scientifically defensible method for comparing, reconciling, and combining active fire observations from MODIS (Moderate Resolution Imaging Spectroradiometer) and VIIRS (Visible Infrared Imaging Radiometer Suite) into a unified, consistent burning activity dataset.

Simply concatenating MODIS and VIIRS CSV files produces severe bias:
- **Footprint Asymmetry**: VIIRS 375m pixels cover ~0.14 km² at nadir, whereas MODIS 1km pixels cover ~1.0 km² at nadir, expanding to ~9.6 km² at scan edge ("bow-tie" effect).
- **Sub-Pixel Sensitivity**: VIIRS detects small, cooler agricultural residue fires (~10-20 m²) that fall below the MODIS detection threshold. VIIRS routinely reports 3x to 6x more discrete active fire detections than MODIS over identical agricultural burn events.
- **Overpass Geometry**: While Aqua and NOAA-20 both have afternoon overpasses (~1:30 PM local equator crossing), Terra passes in the morning (~10:30 AM), capturing different diurnal stages of agricultural burning.

---

## 2. Harmonization Architecture

```
Raw MODIS Points (1000m)           Raw VIIRS Points (375m)
        |                                   |
        v                                   v
+-------------------------------------------------------------+
|             Canonical Normalization & UTC Alignment          |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|             Configurable Spatial Grid Binning               |
|            (Default: 0.05° x 0.05° ≈ 5 km Cells)            |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|          Cross-Sensor Spatial & Temporal Association        |
|  Spatial Distance <= 1.5 km  |  Time Difference <= 3.0 hrs  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              Sensor Normalization & Intercalibration        |
|  • Wooster et al. (2021) Calibrated FRP Regression          |
|  • Effective Multi-Sensor Detection Weighting               |
|  • Sensor Consensus Score [0.0, 1.0]                        |
|  • Normalized Burning Activity Index [0.0, 100.0]           |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 Harmonized Observation Grid                 |
|  Stored in `harmonized_observations` with provenance        |
+-------------------------------------------------------------+
```

---

## 3. Mathematical & Scientific Formulations

### 3.1 Spatial Framework
Continuous geographic coordinates are projected into discrete global grid cells:
$$\text{GridLat} = \lfloor \text{Lat} / \Delta_{\text{deg}} \rfloor \cdot \Delta_{\text{deg}}$$
$$\text{GridLon} = \lfloor \text{Lon} / \Delta_{\text{deg}} \rfloor \cdot \Delta_{\text{deg}}$$
where $\Delta_{\text{deg}}$ is the configurable spatial resolution (default $0.05^\circ \approx 5\text{ km}$ at $30^\circ\text{N}$). Each cell has a deterministic identifier: `grid_{GridLat}_{GridLon}`.

### 3.2 Cross-Sensor Association Metric
For every MODIS observation $M_i$ and VIIRS observation $V_j$ within cell $C$ on date $D$:
$$\text{Associated}(M_i, V_j) \iff d_{\text{Haversine}}(M_i, V_j) \le \delta_{\text{dist}} \quad \land \quad |\Delta t(M_i, V_j)| \le \delta_{\text{time}}$$
- Default spatial threshold: $\delta_{\text{dist}} = 1.5\text{ km}$ (encompassing MODIS 1km footprint plus geolocation uncertainty).
- Default temporal threshold: $\delta_{\text{time}} = 3.0\text{ hours}$ (encompassing afternoon overpass concurrence between Aqua and NOAA-20).

### 3.3 Fire Radiative Power (FRP) Intercalibration
Following empirical regression benchmarks (Wooster et al., 2021; Schroeder et al., 2014):
$$\text{FRP}_{\text{calibrated}} = \sum_{i} \text{FRP}_{M_i} + \beta \sum_{j} \text{FRP}_{V_j}$$
where $\beta = 1.04$ is the configurable VIIRS FRP calibration slope reconciling sub-pixel saturation differences.

### 3.4 Sensor Consensus Score
The consensus score $S_{\text{consensus}} \in [0.0, 1.0]$ measures agreement between sensors:
$$S_{\text{consensus}} = 
\begin{cases}
0.70 + 0.30 \times \min\left(1.0, \frac{N_{\text{associated}}}{\min(N_{\text{MODIS}}, N_{\text{VIIRS}})}\right) & \text{if } N_{\text{MODIS}} > 0 \land N_{\text{VIIRS}} > 0 \\
0.75 & \text{if } N_{\text{MODIS}} = 0 \land N_{\text{VIIRS}} \ge 2 \\
0.60 & \text{if } N_{\text{MODIS}} = 0 \land N_{\text{VIIRS}} = 1 \\
0.55 & \text{if } N_{\text{MODIS}} > 0 \land N_{\text{VIIRS}} = 0
\end{cases}$$

### 3.5 Normalized Burning Activity Index (NBAI)
To provide an operational index ($0$ to $100$) reflecting burning intensity independent of sensor quirks:
$$N_{\text{effective}} = w_{\text{MODIS}} \times N_{\text{MODIS}} + N_{\text{VIIRS}}$$
$$\text{DetectionTerm} = \min(C_{\text{det}}, N_{\text{effective}} \times s_{\text{det}})$$
$$\text{EnergyTerm} = \min(C_{\text{FRP}}, \ln(1 + \text{FRP}_{\text{calibrated}}) \times s_{\text{FRP}})$$
$$\text{ConsensusTerm} = S_{\text{consensus}} \times W_{\text{consensus}}$$
$$\text{NBAI} = \min(100.0, \text{DetectionTerm} + \text{EnergyTerm} + \text{ConsensusTerm})$$

**Authoritative Parameters (ConfigManager Registry):**
All parameters carry scientific provenance and are configurable at runtime without code modification:
- $w_{\text{MODIS}} = 2.5$ (`nasa.harmonization.modis_detection_weight`): Footprint area weighting accounting for the ~7x larger area of 1km MODIS pixels relative to 375m VIIRS pixels.
- $s_{\text{det}} = 3.5$ (`nasa.harmonization.detection_index_slope`): Sensitivity scaling per effective detection.
- $C_{\text{det}} = 50.0$ (`nasa.harmonization.detection_index_cap`): Detection term saturation limit.
- $s_{\text{FRP}} = 7.0$ (`nasa.harmonization.frp_index_slope`): Logarithmic energy scaling slope.
- $C_{\text{FRP}} = 35.0$ (`nasa.harmonization.frp_index_cap`): Energy term saturation limit.
- $W_{\text{consensus}} = 15.0$ (`nasa.harmonization.consensus_index_weight`): Inter-sensor consensus maximum contribution.

### 3.6 Grid Geometry & Coordinate Projection Caveat
At mid-latitudes such as Punjab ($30^\circ\text{N}$):
- $1^\circ \text{ latitude} \approx 111.0\text{ km} \implies 0.05^\circ \approx 5.55\text{ km}$
- $1^\circ \text{ longitude} \approx 111.0 \times \cos(30^\circ) \approx 96.1\text{ km} \implies 0.05^\circ \approx 4.81\text{ km}$
Each $0.05^\circ \times 0.05^\circ$ grid cell forms a rectangle of approximately $5.55\text{ km} \times 4.81\text{ km} \approx 26.7\text{ km}^2$. All spatial distance tests within cells use true geodesic Haversine distance rather than planar approximations.

---

## 4. Uncertainty & Coverage Categorization

The engine rigorously distinguishes satellite observation coverage from burning activity:
- `DUAL_SENSOR`: Both MODIS and VIIRS detected active fire in the same grid cell and time window; lowest uncertainty ($S_{\text{consensus}} \ge 0.85$).
- `VIIRS_ONLY`: Active fire detected exclusively by VIIRS (typically small or cool agricultural residue fires below MODIS sensitivity).
- `MODIS_ONLY`: Detected exclusively by MODIS (often indicating cloud obstruction during VIIRS overpass or edge-of-swath scan divergence).
- `ZERO_BURNING`: Observations were ingested within the bounding box on that date, but no active fires were detected in the cell.
- `NO_OVERPASS`: No satellite observations were recorded in the database for the given date and spatial bounding box.

### 4.1 Temporal Aggregation Granularities
The Activity Calendar aggregates harmonized records across four continuous granularities:
1. **Daily**: Continuous sequence of calendar dates with day-of-week, detections breakdown, and coverage status.
2. **Weekly**: Continuous ISO-8601 weeks (1–52/53) with total detections, peak dates, and mean activity index.
3. **Monthly**: Calendar months (January–December) with active burning days and peak detection counts.
4. **Annual**: Full annual cycle with automatic detection of the Kharif burning season boundaries (October 1 – November 30) and season peak date.
