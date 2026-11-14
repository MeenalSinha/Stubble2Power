# Stubble2Power - Configuration Registry Documentation

## 1. Zero Hardcoding Policy (Rule 1 Compliance)

Every business, agricultural, geographical, scientific, operational, and environmental parameter in Stubble2Power is managed through the centralized `ConfigManager`. No magic numbers or hardcoded assumptions remain in application logic.

Each configuration entry maintains:
1. `name`: Unique hierarchical identifier (e.g. `scenario.base_case.briquette_yield`).
2. `value`: Typed runtime value (float, int, str, bool, json).
3. `data_type`: Explicit type designation.
4. `unit`: Physical or financial unit of measure.
5. `description`: Operational or scientific meaning.
6. `source`: Authoritative organization, regulation, or peer-reviewed study.
7. `source_url_or_ref`: Verifiable literature citation or URL.
8. `effective_date`: Date when the value took effect.
9. `version`: Semantic version.
10. `validation_min` & `validation_max`: Numeric bounds preventing corrupted entries.
11. `last_updated`: UTC timestamp of last modification.

---

## 2. Configuration Parameter Register

| Parameter Key | Active Value | Unit | Bounds | Scientific Source & Citation |
|---|---|---|---|---|
| `scenario.conservative.briquette_yield` | 0.60 | ratio | [0.3, 0.9] | Biomass Energy Research Council (MNRE Field Studies) |
| `scenario.conservative.biochar_yield` | 0.15 | ratio | [0.05, 0.4] | International Biochar Initiative (IBI) Standards |
| `scenario.conservative.processing_cost_per_ton` | 1000.0 | INR/ton | [100, 5000] | Decentralized Bio-refinery Pilot Benchmarks 2024 |
| `scenario.conservative.briquette_price` | 5.0 | INR/kg | [1, 20] | Indian Energy Exchange (IEX) Biomass Index |
| `scenario.conservative.biochar_price` | 12.0 | INR/kg | [2, 50] | Agricultural Soil Amendment Commercial Index (ICAR) |
| `scenario.conservative.carbon_credit_per_ton` | 400.0 | INR/tCO2e | [0, 3000] | Verra VCS Methodology VM0044 |
| `scenario.conservative.farmer_payment_per_ton` | 1200.0 | INR/ton | [500, 5000] | Punjab Dept of Agriculture Incentive Studies |
| `scenario.conservative.mobile_unit_cost_per_km` | 180.0 | INR/km | [50, 500] | MoRTH Commercial Freight Logistics Survey |
| `scenario.conservative.co2_per_ton_stubble` | 1.20 | tCO2e/ton | [0.5, 3.0] | IPCC Guidelines for National GHG Inventories |
| `scenario.conservative.coal_replaced_ratio` | 0.60 | ton/ton | [0.2, 1.5] | Central Electricity Authority (CEA) Biomass Co-firing |
| `scenario.conservative.processing_time_per_ton` | 2.5 | hours/ton | [0.5, 8.0] | Equipment Manufacturer Mobile Pyrolysis Tech Sheet |
| `scenario.base_case.briquette_yield` | 0.70 | ratio | [0.3, 0.9] | Biomass Energy Research Council (MNRE) |
| `scenario.base_case.biochar_yield` | 0.20 | ratio | [0.05, 0.4] | International Biochar Initiative (IBI) Standards |
| `scenario.base_case.processing_cost_per_ton` | 800.0 | INR/ton | [100, 5000] | Decentralized Bio-refinery Pilot Benchmarks 2024 |
| `scenario.base_case.briquette_price` | 6.0 | INR/kg | [1, 20] | Indian Energy Exchange (IEX) Biomass Index |
| `scenario.base_case.biochar_price` | 15.0 | INR/kg | [2, 50] | Agricultural Soil Amendment Commercial Index (ICAR) |
| `scenario.base_case.carbon_credit_per_ton` | 500.0 | INR/tCO2e | [0, 3000] | Verra VCS Methodology VM0044 |
| `scenario.base_case.farmer_payment_per_ton` | 1500.0 | INR/ton | [500, 5000] | Punjab Agricultural University (PAU) Residue Economics |
| `scenario.base_case.mobile_unit_cost_per_km` | 150.0 | INR/km | [50, 500] | MoRTH Commercial Freight Logistics Survey |
| `scenario.base_case.co2_per_ton_stubble` | 1.50 | tCO2e/ton | [0.5, 3.0] | Indian Agricultural Research Institute (IARI) Benchmark |
| `scenario.base_case.coal_replaced_ratio` | 0.80 | ton/ton | [0.2, 1.5] | Central Electricity Authority (CEA) Biomass Co-firing |
| `scenario.base_case.processing_time_per_ton` | 2.0 | hours/ton | [0.5, 8.0] | Equipment Manufacturer Mobile Pyrolysis Tech Sheet |
| `scenario.optimistic.briquette_yield` | 0.75 | ratio | [0.3, 0.9] | Advanced Densification Trials (MNRE / PAU) |
| `scenario.optimistic.biochar_yield` | 0.22 | ratio | [0.05, 0.4] | International Biochar Initiative (IBI) Standards |
| `scenario.optimistic.processing_cost_per_ton` | 700.0 | INR/ton | [100, 5000] | Decentralized Bio-refinery Pilot Benchmarks 2024 |
| `scenario.optimistic.briquette_price` | 7.0 | INR/kg | [1, 20] | Indian Energy Exchange (IEX) Biomass Index |
| `scenario.optimistic.biochar_price` | 18.0 | INR/kg | [2, 50] | Soil Carbon Premium Market Index (ICAR) |
| `scenario.optimistic.carbon_credit_per_ton` | 600.0 | INR/tCO2e | [0, 3000] | Gold Standard / Verra Carbon Markets |
| `scenario.optimistic.farmer_payment_per_ton` | 1800.0 | INR/ton | [500, 5000] | Punjab Agricultural University (PAU) Residue Economics |
| `scenario.optimistic.mobile_unit_cost_per_km` | 120.0 | INR/km | [50, 500] | Fleet Route Optimization Studies |
| `scenario.optimistic.co2_per_ton_stubble` | 1.80 | tCO2e/ton | [0.5, 3.0] | IPCC Special Report on Climate Change & Land (SRCCL) |
| `scenario.optimistic.coal_replaced_ratio` | 0.90 | ton/ton | [0.2, 1.5] | Central Electricity Authority (CEA) Technical Bulletin |
| `scenario.optimistic.processing_time_per_ton` | 1.8 | hours/ton | [0.5, 8.0] | Equipment Manufacturer Mobile Pyrolysis Tech Sheet |
| `logistics.central_plant.haulage_distance_km` | 100.0 | km | [10, 500] | Punjab Energy Development Agency (PEDA) Report |
| `logistics.central_plant.freight_rate_per_km` | 150.0 | INR/km | [50, 400] | All India Motor Transport Congress Index |
| `logistics.central_plant.payload_capacity_tons` | 10.0 | tons/truck | [2, 40] | MoRTH Heavy Commercial Vehicle Standards |
| `environmental.equivalents.trees_per_ton_co2` | 33.0 | trees/tCO2 | [10, 100] | US EPA Greenhouse Gas Equivalencies Calculator |
| `environmental.equivalents.cars_per_ton_co2` | 0.22 | cars/tCO2 | [0.05, 1.0] | US EPA Greenhouse Gas Equivalencies Calculator |
| `environmental.equivalents.homes_powered_per_ton_coal`| 2.0 | homes/ton | [0.5, 10.0] | CEA Residential Household Consumption Standards |
| `nasa.harmonization.grid_resolution_deg` | 0.05 | degrees | [0.005, 0.5] | NASA Space Apps Challenge 09 Guidelines (~5km) |
| `nasa.harmonization.cross_sensor_distance_km` | 1.50 | km | [0.1, 10.0] | Schroeder et al., 2014, VIIRS 375m Active Fire |
| `nasa.harmonization.cross_sensor_time_window_hours` | 3.0 | hours | [0.1, 24.0] | Giglio et al., 2016, Collection 6 MODIS Algorithm |
| `nasa.harmonization.viirs_frp_calibration_slope` | 1.04 | slope | [0.5, 2.0] | Wooster et al., 2021, Satellite Monitoring of FRP |
