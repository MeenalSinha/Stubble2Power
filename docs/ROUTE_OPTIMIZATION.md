# Rural Road Network Routing & Vehicle Optimization Methodology
## Phase 11: Transport Logistics with Road Tortuosity Modeling

---

## 1. Rural Road Circuitousness & Tortuosity Modeling

A common failure in academic geospatial logistics models is substituting straight-line Euclidean or Great-Circle (haversine) distances for rural freight transit. In rural India, especially the canal-fed agricultural landscapes of Punjab and Haryana, roads follow irrigation field boundaries, canal bridges, and village bypasses.

Straight-line distance severely underestimates actual driving distance and fuel costs by $25\text{--}40\%$.

### National Rural Infrastructure Development Agency (NRIDA) PMGSY Calibration
Stubble2Power integrates a calibrated **Road Network Tortuosity Ratio**:
$$\text{Road Distance (km)} = \text{Geodesic Distance (km)} \times \tau$$

Where:
- $\tau = 1.35$ (Calibrated Pradhan Mantri Gram Sadak Yojana rural link road tortuosity factor).
- Transit Speed: $35.0\text{ km/h}$ average tractor-trailer operating speed on rural single-lane roads.
- Fuel Consumption Rate: $0.32\text{ liters diesel / km}$ (`refinery.transport.fuel_consumption_liters_per_km`).

$$\text{Travel Duration (hours)} = \frac{\text{Road Distance (km)}}{\text{Transit Speed (km/h)}}$$
$$\text{Diesel Fuel Consumed (liters)} = \text{Road Distance (km)} \times 0.32\text{ L/km}$$
$$\text{Logistics Transport Cost (INR)} = \text{Fuel Consumed} \times \text{Diesel Retail Price (INR/L)}$$

---

## 2. Multi-Unit Capacity-Constrained Deployment Planner

The deployment planner solves a multi-objective capacity allocation problem across available mobile bio-refineries and candidate farm parcels:

### Operational Constraints
1. **Daily Processing Throughput:** Each unit $u$ has daily capacity $C_u = \text{hourly\_capacity} \times \text{operating\_hours}$ (e.g. $25\text{ t/day}$).
2. **Campaign Duration:** Window $D = (\text{date\_end} - \text{date\_start}) + 1$ days. Maximum capacity $= C_u \times D$.
3. **Maximum Operating Radius:** Farm parcel $f$ must lie within $R_u$ (default $50\text{--}60\text{ km}$) of unit home depot:
   $$\text{Haversine}(f, u_{\text{depot}}) \le R_u$$

### Optimization Strategies
- **`BALANCED`:** Primary sorting by biomass volume descending, with distance ties broken by nearest depot.
- **`MAX_BIOMASS`:** Prioritizes largest farm aggregations first to maximize total diverted stubble tonnage.
- **`MIN_COST`:** Prioritizes farms closest to home depots to minimize total road diesel expenditure.

---

## 3. Vehicle Route Sequencing (2-Opt / Nearest-Neighbor CVRP)

For each mobile unit with assigned collection parcels:
1. Route initializes at unit's home depot (`DEPOT_START`).
2. Parcels are sequenced using a nearest-neighbor heuristic based on road distance matrix.
3. Each stop logs sequence number, action (`FARM_COLLECTION`), assigned payload (tons), and leg road distance.
4. Route terminates with return leg to home depot (`DEPOT_END`).

---

## 4. Unserved Farms Transparency

If regional candidate biomass exceeds total fleet processing capacity, or if farms lie beyond the maximum travel radius:
- The system **never silences or fakes capacity**.
- Unserved parcels are transparently recorded in `DeploymentPlan.parameters_json["unserved_details"]` with farm ID, coordinates, unserved biomass tonnage, and specific diagnostic rejection reason (`OUT_OF_RANGE_OR_FLEET_AT_CAPACITY`).
