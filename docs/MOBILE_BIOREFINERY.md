# Mobile Bio-Refinery Fleet & Technology Specification
## Phase 11: Decentralized Processing & Conversion Engineering

---

## 1. System Vision: Decentralized vs. Centralized Processing

Conventional biomass power models rely on massive centralized thermal plants ($10\text{--}50\text{ MW}$) requiring agricultural straw to be transported $50\text{--}80\text{ km}$ across rural link roads. Because raw stubble has extremely low bulk density ($40\text{--}60\text{ kg/m}^3$), transporting loose or baled straw over long distances creates:
1. Prohibitive logistics costs ($>60\%$ of total operating budget).
2. Rural road traffic congestion and link road destruction.
3. Severe transport carbon footprints that negate project climate benefits.

**Stubble2Power's Paradigm:** Trailer-mounted mobile bio-refineries travel directly to rural farm clusters. Dense energy products (briquettes at $1,000\text{--}1,200\text{ kg/m}^3$ and biochar) are produced in-situ within hours of harvest, reducing transport volume requirements by up to $70\%$.

---

## 2. Fleet Specifications & Equipment Profiles

### Unit Class A: Trailer-Mounted Mechanical Densifier (Briquetter)
- **Equipment Type:** `TRAILER_MOUNTED_DENSIFIER`
- **Conversion Technology:** High-pressure mechanical piston/screw densification (`BRIQUETTING`).
- **Hourly Throughput:** $2.5\text{ tonnes/hour}$ raw conditioned stubble.
- **Daily Operating Schedule:** $10.0\text{ operating hours/day}$ ($25.0\text{ tonnes/day}$ capacity).
- **Auxiliary Fuel Consumption:** $4.5\text{ liters diesel / ton processed}$ (generator-driven hydraulic press).
- **Direct Hourly Operating Cost:** $\text{INR } 750\text{/hour}$ (field operator crew and consumable press dies).
- **Output Product:** Industrial biomass briquettes ($70\text{--}85\%$ conversion mass yield, calorific value $\sim 3,400\text{--}3,600\text{ kcal/kg}$).

### Unit Class B: Trailer-Mounted Mobile Pyrolysis Rig
- **Equipment Type:** `TRAILER_MOUNTED_PYROLYZER`
- **Conversion Technology:** Slow anaerobic pyrolysis (`SLOW_PYROLYSIS`).
- **Hourly Throughput:** $1.5\text{ tonnes/hour}$.
- **Daily Operating Schedule:** $10.0\text{ operating hours/day}$ ($15.0\text{ tonnes/day}$ capacity).
- **Auxiliary Fuel Consumption:** $3.8\text{ liters diesel / ton processed}$.
- **Direct Hourly Operating Cost:** $\text{INR } 900\text{/hour}$.
- **Output Product:** Soil-enhancement grade agricultural biochar ($20\text{--}30\%$ conversion mass yield, $72\%$ persistent stable carbon).

---

## 3. Fleet Operational States

| Status | Definition |
|---|---|
| `AVAILABLE` | Deployed at regional home depot, serviced, ready for deployment assignment. |
| `DEPLOYED` | Active on a multi-stop field collection and processing campaign. |
| `MAINTENANCE` | Undergoing die replacement, hydraulic fluid flush, or mechanical overhaul. |
| `STANDBY` | Reserve capacity for high-density fire anomaly emergency response. |
