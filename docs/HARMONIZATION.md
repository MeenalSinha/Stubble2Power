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
To provide an operational index (0 to 100) reflecting burning intensity independent of sensor quirks:
$$N_{\text{effective}} = 2.5 \times N_{\text{MODIS}} + N_{\text{VIIRS}}$$
$$\text{DetectionTerm} = \min(50.0, N_{\text{effective}} \times 3.5)$$
$$\text{EnergyTerm} = \min(35.0, \ln(1 + \text{FRP}_{\text{calibrated}}) \times 7.0)$$
$$\text{ConsensusTerm} = S_{\text{consensus}} \times 15.0$$
$$\text{NBAI} = \min(100.0, \text{DetectionTerm} + \text{EnergyTerm} + \text{ConsensusTerm})$$

---

## 4. Uncertainty & Coverage Categorization

The engine distinguishes:
- `DUAL_SENSOR`: Both sensors confirmed active burning; lowest uncertainty.
- `VIIRS_ONLY`: Active fire detected exclusively by VIIRS (small/cool sub-pixel agricultural residue fire).
- `MODIS_ONLY`: Detected exclusively by MODIS (often indicating cloud obstruction during VIIRS overpass or edge-of-swath scan divergence).
- `ZERO_DETECTED`: Clear satellite overpass with zero detected fires.
- `NO_OVERPASS`: Incomplete satellite swath coverage or thick persistent cloud cover preventing observation.
