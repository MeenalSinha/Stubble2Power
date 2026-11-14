# Seasonal Fire Intelligence Architecture

## 1. Overview & Purpose
Agricultural burning follows rigorous climatological and agronomic cycles tied to crop harvesting seasons.
In Northwestern India (Punjab & Haryana), satellite fire activity exhibits distinct bi-modal annual seasonality:
- **Kharif Post-Harvest Window (Oct 01 – Nov 30)**: Extensive paddy residue burning driven by a tight 2-3 week planting turnaround before winter wheat sowing.
- **Rabi Post-Harvest Window (Apr 10 – May 25)**: Wheat stubble burning prior to Kharif monsoon preparation.

The Seasonal Fire Intelligence subsystem (`backend/services/seasonal/`) transforms discrete daily harmonized NASA MODIS & VIIRS observations into continuous, empirical seasonal profiles and multi-year statistical normals.

---

## 2. Mathematical & Scientific Methodology

### 2.1 Multi-Year Baseline Computation
For each day of year $d \in [1, 365]$ (standardized to 365 days across leap years), the historical baseline engine computes both parametric and non-parametric statistics across $N$ historical seasons:

$$\mu_d = \frac{1}{N} \sum_{i=1}^N x_{i, d}$$

$$\sigma_d = \sqrt{\frac{1}{N-1} \sum_{i=1}^N (x_{i, d} - \mu_d)^2}$$

$$\text{Median}_d = \text{median}(\{x_{1, d}, \dots, x_{N, d}\})$$

$$\text{MAD}_d = 1.4826 \times \text{median}(|x_{i, d} - \text{Median}_d|)$$

Where:
- $1.4826$ is the normal distribution consistency scale factor.
- Median Absolute Deviation (MAD) provides outlier resistance against extreme, single-day fire spikes.

### 2.2 Empirical Seasonal Dynamics & S-Curve Distribution
For any specified regional window, the cumulative fire activity $C(t)$ is evaluated:

$$C(t) = \sum_{\tau = t_0}^t A(\tau)$$

- **Season Onset Date**: $t_{\text{onset}} = \min \{ t \mid C(t) \ge 0.10 \times C(t_{\text{end}}) \}$
- **Peak Date**: $t_{\text{peak}} = \arg\max_t A(t)$
- **Season Decay Date**: $t_{\text{decay}} = \min \{ t \ge t_{\text{peak}} \mid C(t) \ge 0.90 \times C(t_{\text{end}}) \}$
- **Season Duration**: $D = t_{\text{decay}} - t_{\text{onset}} + 1$

---

## 3. Data Sufficiency Protocol
Per WMO and NASA Earth Science protocols, baselines cannot be asserted without adequate observation coverage:
1. `SUFFICIENT`: Sample count $\ge N_{\min}$ (default 3 historical periods) and observation coverage $\ge 60\%$.
2. `LIMITED_HISTORY`: Sample count $< 3$ periods.
3. `INSUFFICIENT_COVERAGE`: Observation overpass ratio $< 60\%$.

---

## 4. REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/seasonal/profiles` | `GET` | Retrieves active empirical seasonal profiles. |
| `/api/seasonal/profiles/generate` | `POST` | Generates empirical onset, peak, and decay dates for a given window. |
| `/api/seasonal/baselines` | `GET` | Lists multi-year normals (mean, median, MAD, percentiles). |
| `/api/seasonal/baselines/compute` | `POST` | Computes baseline normals from historical observations. |
