# Stubble2Power — User Operational Guides

**Document ID:** S2P-DOC-USR-GUI-2026-V1  
**Classification:** Operational User Manuals  
**Platform Version:** v2.5.0  

---

## Guide 1: Farmer & Landholder Operational Manual

### 1.1 Overview
As a farmer, Stubble2Power allows you to turn crop residue (paddy stubble, wheat straw, cotton stalks) into a clean, profitable resource. Instead of burning stubble in the open field, you can schedule on-site collection by a mobile bio-refinery, receive direct per-ton compensation, and protect rural air quality.

### 1.2 Step-by-Step Workflow
1. **Account Registration & Login:**
   - Navigate to the **Login & Identity** tab.
   - Register using your mobile phone or email. Select the role **FARMER**.
   - Your account is isolated within your local district or agricultural cooperative society.
2. **Registering Landholdings & Parcels:**
   - Under the **Farmer Management** tab, register your agricultural parcel.
   - Provide your village name, district, total land area in acres, soil type, and GPS coordinates (or select on the interactive map).
3. **Recording Crop Cultivation & Harvest Dates:**
   - Add your seasonal crop record (e.g., Kharif Paddy Rice, Rabi Wheat).
   - Enter your anticipated or actual harvest date and expected grain yield in metric tons.
   - The platform automatically calculates your residue biomass using Punjab Agricultural University (PAU) Residue-to-Product Ratios (RPR = 1.15 for paddy).
4. **Managing Statutory Consent (DPDP Act 2023):**
   - Under **Privacy & Consent**, grant or withdraw specific permissions:
     - `BIOMASS_AGGREGATION`: Authorizes stubble quantity estimation.
     - `LOGISTICS_DISPATCH`: Authorizes tractor-trailer entry for pickup.
     - `COMMUNICATION_SMS`: Authorizes pickup scheduling alerts.
   - You may withdraw consent at any time; your parcels will immediately be excluded from automated collection route dispatches.
5. **Payment Tracking:**
   - Once your stubble is weighed and collected, your account reflects the collected tonnage and the guaranteed farmer incentive payment (₹1,500 – ₹1,800 per ton).

---

## Guide 2: Fleet & Logistics Operator Manual

### 2.1 Overview
Fleet operators manage mobile bio-refinery units, vehicle depots, collection schedules, and road-routing logistics.

### 2.2 Step-by-Step Workflow
1. **Registering Mobile Bio-Refineries:**
   - In the **Mobile Bio-Refinery & Routing** workspace, register mobile units.
   - Specify machine specifications:
     - `Hourly Capacity`: (e.g., 3.0 metric tons/hour).
     - `Daily Operating Hours`: (e.g., 10 hours/day).
     - `Home Depot Coordinates`: (Latitude, Longitude of base depot).
     - `Maximum Travel Radius`: (e.g., 100 km).
     - `Operating Cost`: Hourly rate and fuel consumption coefficients.
2. **Generating Optimized 2-Opt Routing Schedules:**
   - Select your target deployment date window and district (e.g., Ludhiana, October 20 to November 15).
   - Click **Generate Optimized Deployment Plan**.
   - The engine clusters consented candidate farms, respects machine daily throughput, and runs a 2-Opt Traveling Salesperson (TSP) heuristic adjusted for rural road tortuosity ($\tau = 1.35$).
3. **Dispatching Vehicles & Managing Turnaround:**
   - Review the sequenced waypoint map showing depot departure, farm-by-farm collection stops, and return.
   - Export driver waypoints and track fuel consumption in liters.
   - As trucks complete collection, update the parcel status from `SCHEDULED` to `PICKED_UP` and `PROCESSED`.

---

## Guide 3: Bio-Refinery Plant & Operations Manager Manual

### 3.1 Overview
Plant managers monitor decentralized processing operations, feedstock inventory stages, and techno-economic returns.

### 3.2 Step-by-Step Workflow
1. **Biomass Inventory Reconciliation:**
   - In the **Biomass Inventory** view, track biomass through 5 lifecycle stages:
     - `IDENTIFIED`: Satellite- or farmer-reported stubble available in fields.
     - `ALLOCATED`: Assigned to a scheduled mobile refinery route.
     - `COLLECTED`: Picked up from the farm parcel.
     - `PROCESSED`: Converted into densified briquettes, pellets, or biochar.
     - `DISTRIBUTED`: Sold to industrial boilers, thermal plants, or soil amendment buyers.
2. **Techno-Economic DCF Feasibility:**
   - Navigate to the **Techno-Economic & LCA** tab.
   - Choose a preset scenario (`Base Case`, `High Oil / Coal Spike`, `Fodder Scarcity`, `Carbon Market Boom`) or configure custom pricing.
   - Review multi-year Capital Budgeting metrics:
     - **Net Present Value (NPV)**: Discounted at 10.5% WACC over 10 project years.
     - **Internal Rate of Return (IRR)**: Capital efficiency metric.
     - **Levelized Cost of Energy (LCOE)**: Processing cost per ton.
     - **Break-Even Tonnage**: Minimum throughput needed to cover annual fixed charges.
3. **Sensitivity Analysis:**
   - Inspect the automated Tornado diagram showing which input parameters (briquette selling price, farmer incentives, diesel costs) have the highest leverage on operating margins.

---

## Guide 4: Environmental & Carbon Credit Analyst Manual

### 4.1 Overview
Environmental analysts and MRV (Measurement, Reporting, and Verification) auditors track fire abatement, verify baseline burning emissions, and quantify carbon credits.

### 4.2 Step-by-Step Workflow
1. **Monitoring NASA Satellite Fire Intelligence:**
   - Navigate to **Satellite Fire Intelligence**.
   - Inspect synchronized NASA FIRMS observations (MODIS Terra/Aqua and VIIRS NOAA-20/Suomi-NPP).
   - View the active fire layers, thermal anomaly clusters, and Fire Radiative Power (FRP in Megawatts).
2. **Running Cross-Sensor Harmonization:**
   - In the **Harmonization Engine**, execute cross-sensor coincidence matching.
   - Examine candidate pairs linked across the $1.5\text{ km} / 3.0\text{ h}$ window with Wooster et al. linear FRP cross-calibration ($\beta = 1.04$).
   - Review Normalized Burned Area Index (NBAI) and Sensor Consensus Confidence scores.
3. **Statistical Anomaly & Seasonal Spike Detection:**
   - Review the **Seasonal & Historical Calendar** to observe Kharif burning peak timing.
   - Use the **Anomaly Detector** to isolate anomalous high-intensity clusters ($Z \ge 2.0$) exceeding 5-year historical medians.
4. **Cradle-to-Grave Life Cycle Assessment (LCA):**
   - Open the **Life Cycle Assessment** dashboard.
   - Review ISO 14040/14044 emissions balances computed using IPCC AR6 GWP100 metrics:
     - Baseline Field Combustion Avoidance ($1,554.4\text{ kg } \text{CO}_2\text{e}$ per ton).
     - Transport Logistics Diesel Footprint ($2.68\text{ kg } \text{CO}_2$ per liter).
     - Thermal Coal Replacement ($0.98\text{ t } \text{CO}_2\text{e}$ per ton of briquettes).
     - Biochar 100-Year Recalcitrant Sequestration ($2.20\text{ t } \text{CO}_2\text{e}$ per ton of biochar).
   - Download certified additionality dossiers formatted for Verra VCS VM0044 and Puro.earth methodologies.

---

## Guide 5: System Administrator & Compliance Officer Manual

### 5.1 Overview
System administrators govern identity, role-based access control (RBAC), multi-tenant organization isolation, audit log integrity, and DPDP Act compliance.

### 5.2 Step-by-Step Workflow
1. **User & Organization Administration:**
   - In the **Administration & Governance** tab, manage user accounts and assign explicit RBAC roles:
     - `SYSTEM_ADMINISTRATOR`: Full root governance.
     - `ORGANIZATION_MANAGER`: Cooperative-level management.
     - `ENVIRONMENTAL_ANALYST`: Remote sensing and LCA access.
     - `AGRICULTURAL_ANALYST`: Agronomy and farm data access.
     - `FIELD_OPERATOR`: Fleet and logistics execution.
     - `FARMER`: Farm landholdings and consent controls.
     - `PUBLIC_VISITOR`: Read-only, obfuscated public views.
2. **Enforcing Geospatial Privacy & Obfuscation:**
   - Verify that non-consented or public satellite queries route through the metric tensor obfuscator (~1.1 km coordinate truncation) to protect private farm parcels.
3. **Processing Data Subject Requests (DSR):**
   - Review pending DPDP Section 11/12 requests (`ACCESS`, `CORRECTION`, `ERASURE`, `EXPORT`).
   - Trigger approved erasure or data portability exports with automated audit trail logging.
4. **Immutable Audit Log Review:**
   - Inspect system security events and audit records.
   - Attempting to modify or delete audit log entries is strictly rejected by SQLAlchemy database triggers, guaranteeing tamper resistance.
5. **System Configuration & Backup Operations:**
   - Inspect and adjust system parameters via the **Configuration Registry**.
   - Verify daily automated backup snapshots and test cryptographic SHA-256 restoration scripts.
