# Stubble2Power - User Roles & Operational Workflows

## 1. Overview
Stubble2Power is built around distinct operational personas. Each persona has a dedicated workspace tailored to their specific technical requirements, legal responsibilities, and decision-making workflows.

---

## 2. Seven Persona Workflows

### 2.1 Public Visitor Workflow
```
[Arrive at Public Portal]
         |
         v
[Inspect Obfuscated NASA Fire Map] (2-decimal ~1.1 km privacy filter)
         |
         v
[Review Historical Burning Calendar] (Kharif vs Rabi seasonality)
         |
         v
[Explore Technology & Mission] (Decentralized mobile bio-refineries)
```
- **Objective:** Provide public transparency on stubble burning while safeguarding landholder property privacy.
- **Key Actions:** Pan and zoom the regional satellite map, view FRP intensity distributions, examine clean energy mission.

---

### 2.2 Farmer Workflow
```
[Authenticate Identity] (Gurpreet Singh)
         |
         v
[View Exact Parcel Boundaries] (Unblurred GPS map)
         |
         v
[Submit Harvest Yield Log] (Select farm, enter grain tons, pick date)
         |
         v
[Review Automated Biomass Estimate] (RPR calculation, soil retention)
         |
         v
[Manage DPDP Consents & Rights] (Grant/withdraw purpose consent, submit DSR)
         |
         v
[Inspect Monetization & Earnings] (₹1,800/t price, direct payment terms)
```
- **Objective:** Enable farmers to monetize crop residue easily, access scheduled collection, and manage personal data rights under the DPDP Act 2023.

---

### 2.3 Field Operator Workflow
```
[Check Assigned Equipment] (MBR-PUNJAB-01, 25 t/day Pyrolysis Unit)
         |
         v
[Review 2-Opt Sequenced Stops] (Ludhiana hub -> Farm A -> Farm B -> Hub)
         |
         v
[Update Stop Dispatch Status] (PENDING -> ARRIVED -> PICKED_UP -> PROCESSED)
         |
         v
[Monitor Logistics KPIs] (Transit distance, fuel consumption, carbon savings)
```
- **Objective:** Guide mobile refinery crews along distance-optimized collection routes with live status tracking.

---

### 2.4 Agricultural Analyst Workflow
```
[Consult PAU/ICAR Calendars] (Sowing, harvest, and peak burn windows)
         |
         v
[Test Harvest Window Date] (Active crop evaluation and susceptibility)
         |
         v
[Verify Cropland via LULC] (ESA WorldCover 10m spatial mask query)
         |
         v
[Analyze Regional Biomass Potential] (District-level yield benchmarks)
         |
         v
[Export Agronomic Report] (Auditable CSV / JSON data)
```
- **Objective:** Validate crop phenology, eliminate non-cropland false alarms, and quantify biomass feedstock availability.

---

### 2.5 Environmental Analyst Workflow
```
[Query NASA FIRMS Data] (MODIS 1km & VIIRS 375m active hot spots)
         |
         v
[Run Sensor Harmonization] (Geodesic clustering, FRP weighting)
         |
         v
[Detect Statistical Anomalies] (Z-Score & MAD deviations from 5-yr baseline)
         |
         v
[Execute Cradle-to-Grave LCA] (Open burning avoidance, fuel debits, coal displacement)
         |
         v
[Model Carbon Credits] (Verra VM0044 & Puro.earth carbon credits)
```
- **Objective:** Provide rigorous scientific verification of fire activity and quantify high-integrity carbon reduction additionality.

---

### 2.6 Organization Manager Workflow
```
[Review Cooperative Portfolio] (Enrolled farmers, acreage, pledged biomass)
         |
         v
[Execute Fleet Deployment Planner] (Balanced, Max Biomass, Min Cost)
         |
         v
[Simulate Techno-Economics & DCF] (CAPEX, OPEX, 10% NPV, IRR, Break-even)
         |
         v
[Export Feasibility Dossier] (Bank syndication and subsidy reporting)
```
- **Objective:** Ensure commercial feasibility, maximize fleet utilization, and maintain farmer cooperative profitability.

---

### 2.7 System Administrator Workflow
```
[Manage User Accounts & RBAC] (Assign roles, review MFA status)
         |
         v
[Configure Tenant Organizations] (Tenant codes, domains, memberships)
         |
         v
[Update Dynamic Config Registry] (Zero hardcoding, provenance tracking)
         |
         v
[Audit Immutable System Logs] (Trace security events and state changes)
         |
         v
[Enforce Statutory Retention] (Trigger DPDP compliance sweeps)
```
- **Objective:** Guarantee platform uptime, security governance, parameter transparency, and regulatory compliance.
