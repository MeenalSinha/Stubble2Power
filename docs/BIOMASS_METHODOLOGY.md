# Agricultural Biomass Estimation & Inventory Methodology
## Phase 10: Scientific Formulation & Provenance

---

## 1. Scientific Overview

Agricultural residue is a direct byproduct of crop grain production. However, equating gross crop residue directly to collectable bio-refinery feedstock is scientifically incorrect and agronomically damaging. 

The Stubble2Power Biomass Estimation Engine enforces a multi-tier deduction model:
1. **Gross Residue Generation:** Based on crop-specific Residue-to-Product Ratios (RPR).
2. **In-Situ Soil Conservation Retention:** Essential root, crown, and stubble left in field for organic carbon replenishment and erosion control (25% for paddy).
3. **Competing Demand Deductions:** High-priority local domestic demand, primarily wheat straw used as dairy cattle fodder in Punjab and Haryana (55% to 60%).
4. **Mechanical Collection & Handling Losses:** Raking, baling, and loading field losses (8%).
5. **Moisture Normalization:** Standardized to 14.0% dry storage equilibrium moisture.

---

## 2. Mathematical Equations

### Step 1: Gross Residue Generation
$$\text{Gross Residue (tons)} = \text{Grain Yield (tons)} \times \text{RPR}$$

| Crop Type | Residue-to-Product Ratio (RPR) | Source Benchmark |
|---|---|---|
| **Paddy / Rice (Kharif)** | $1.50$ | ICAR / MNRE Biomass Resource Atlas of India |
| **Wheat (Rabi)** | $1.30$ | Punjab Agricultural University (PAU) |
| **Cotton (Kharif)** | $2.80$ | Central Institute for Cotton Research (CICR) |

### Step 2: Sustainable Collection & Competing Deductions
For **Paddy Straw**:
$$\text{Soil Retention (tons)} = \text{Gross Residue} \times (1.0 - 0.75) = \text{Gross Residue} \times 0.25$$
$$\text{Collectable Residue (tons)} = \text{Gross Residue} \times 0.75$$

For **Wheat Straw**:
$$\text{Competing Dairy Fodder (tons)} = \text{Gross Residue} \times 0.55$$
$$\text{Collectable Residue (tons)} = \text{Gross Residue} \times 0.40$$

### Step 3: Mechanical Collection Losses & Net Usable Biomass
$$\text{Handling Losses (tons)} = \text{Collectable Residue} \times 0.08$$
$$\text{Net Usable Biomass (tons)} = \text{Collectable Residue} - \text{Handling Losses}$$

### Step 4: Dry Matter Accounting
$$\text{Dry Matter (tons)} = \text{Net Usable Biomass} \times \left(1.0 - \frac{\text{Moisture \%}}{100.0}\right)$$

---

## 3. Data Hierarchy for Estimation

To prevent fabricating yield values, the estimation service resolves input data through a strict evidence hierarchy:
1. **Empirical Measured Harvest (`HarvestRecord.actual_grain_yield_tons`):** Confidence = $0.98$.
2. **Farmer Reported Volume (`Farmer.stubble_tons`):** Confidence = $0.85$.
3. **Crop Acreage Baseline (`FarmCrop.expected_yield_tons_per_acre`):** Confidence = $0.75$.
4. **Regional Benchmark Baseline (`ConfigManager.biomass.paddy.default_grain_yield_tons_per_acre`):** Confidence = $0.65$.

---

## 4. Audited Inventory Lifecycle & Allocation Guard

Residue quantities transition across strict audited lifecycle stages:
```
  [ ESTIMATED ] ---> [ CONFIRMED ] ---> [ COMMITTED ] ---> [ ALLOCATED ] ---> [ PROCESSED ]
```
- **Double Allocation Prevention Guard:** When transitioning biomass to `ALLOCATED` or `COMMITTED`, the engine checks the database transaction ledger:
  $$\sum \text{allocated\_tons} + \text{requested\_tons} \le \text{BiomassEstimate.net\_usable\_biomass\_tons}$$
  Any attempt to double-allocate residue raises a `ValidationError` with transaction details.
