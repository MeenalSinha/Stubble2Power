# Scientific Emission Factors & Parameter Provenance Registry
## Master Reference Table for Phases 0–12

---

## 1. Zero-Hardcoding Provenance Table

All domain parameters within Stubble2Power are governed by `ConfigManager` with immutable literature citations, validating ranges, and effective dates.

| Parameter Key | Value | Unit | Scientific Source | Literature Citation / URL |
|---|---|---|---|---|
| `biomass.paddy.residue_to_product_ratio` | $1.50$ | ratio | ICAR / MNRE | Biomass Resource Atlas of India (https://mnre.gov.in) |
| `biomass.wheat.residue_to_product_ratio` | $1.30$ | ratio | Punjab Agricultural University | PAU Research Bulletin on Crop Residues |
| `biomass.cotton.residue_to_product_ratio` | $2.80$ | ratio | ICAR - CICR Nagpur | Central Institute for Cotton Research Technical Bulletin |
| `biomass.paddy.sustainable_collection_fraction` | $0.75$ | fraction | ICAR / PAU Agronomy | 25% minimum soil retention benchmark for soil conservation |
| `biomass.wheat.sustainable_collection_fraction` | $0.40$ | fraction | Punjab State Farmers Commission | 60% priority dairy cattle fodder demand reserve |
| `biomass.collection_handling_loss_fraction` | $0.08$ | fraction | CIAE Bhopal | Mechanical raking and baling handling field losses |
| `biomass.standard_moisture_content_pct` | $14.0$ | % | BIS 17397:2020 | Bureau of Indian Standards Bio-briquette moisture standard |
| `refinery.transport.road_tortuosity_factor` | $1.35$ | ratio | NRIDA / PMGSY | National Rural Infrastructure Development Agency link road study |
| `refinery.transport.fuel_consumption_liters_per_km` | $0.32$ | L/km | CIAE Bhopal | Agricultural tractor laden transit fuel consumption |
| `refinery.mobile.fuel_consumption_liters_per_ton` | $4.50$ | L/t | MNRE Field Benchmarks | Generator auxiliary diesel consumption per ton densified |
| `economics.diesel_price_inr_per_liter` | $89.50$ | INR/L | IOCL Bulletin | Indian Oil Corporation Punjab state retail price benchmark |
| `economics.farmer_procurement_price_per_ton` | $1500.0$ | INR/t | PSPCL / Punjab Policy | Ex-field farmer residue incentive payment standard |
| `economics.discount_rate_wacc_pct` | $10.5$ | % | RBI / IREDA | IREDA Clean Energy Financing Weighted Average Cost of Capital |
| `economics.equipment_depreciation_years` | $7.0$ | years | Companies Act 2013 | Schedule II Plant & Machinery straight-line depreciation |
| `environmental.emission_factor_burning_co2_kg_per_ton` | $1460.0$ | kg/t | IPCC 2006 / Ravindra et al. | IPCC Guidelines Vol 4 Ch 5 / Ravindra et al. (2019) Env Res |
| `environmental.emission_factor_burning_ch4_kg_per_ton` | $2.70$ | kg/t | IPCC 2006 / Andreae (2019) | Andreae (2019) Biomass burning emission factors |
| `environmental.emission_factor_burning_n2o_kg_per_ton` | $0.07$ | kg/t | IPCC 2006 / Ravindra et al. | Incomplete crop residue open combustion emissions |
| `environmental.emission_factor_burning_pm25_kg_per_ton` | $8.30$ | kg/t | CPCB / IIT Delhi | Comprehensive Emissions Inventory for Northern India |
| `environmental.diesel_emission_factor_kg_co2_per_liter` | $2.68$ | kg/L | IPCC 2006 Energy Vol 2 | Automotive diesel mobile combustion emission factor |
| `environmental.gwp_ch4_ar6` | $27.9$ | GWP100 | IPCC AR6 WG1 Table 7.15 | 100-year Global Warming Potential for methane without feedback |
| `environmental.gwp_n2o_ar6` | $273.0$ | GWP100 | IPCC AR6 WG1 Table 7.15 | 100-year Global Warming Potential for nitrous oxide |
| `environmental.coal_displacement_ratio_briquette` | $0.82$ | kg/kg | CEA / NITI Aayog | Thermal power co-firing substitution (3400 vs 4150 kcal/kg) |
| `environmental.coal_emission_factor_kg_co2_per_ton` | $2120.0$ | kg/t | CEA Database Ver 19.0 | CO2 Baseline Database for the Indian Power Sector |
| `environmental.biochar_stable_carbon_fraction` | $0.72$ | fraction | IBI / Lehmann et al. (2021) | 100-year persistent aromatic carbon in slow pyrolysis biochar |
