# Stubble2Power - Data Classification and Retention Architecture

## 1. Overview
This document establishes the data taxonomy, security classification levels, handling controls, and statutory retention schedules across the Stubble2Power platform, in compliance with the Digital Personal Data Protection (DPDP) Act 2023.

---

## 2. Four-Tier Data Classification Taxonomy

### Tier 1: Personal Data & Landholder PII (Confidential / Restricted)
- **Data Elements:** Farmer full names, mobile phone numbers, village addresses, Aadhaar hashes, exact GIS farm parcel coordinates, bank account settlement details.
- **Legal Basis:** Explicit, purpose-bound consent recorded in `ConsentRecord`.
- **Protection Controls:**
  - Masked UI presentation for sensitive identifiers (`XXXX-XXXX-1234`).
  - Spatial obfuscation (truncated to 2 decimal places / ~1.1 km resolution) when exposed to public visitors.
  - Strict tenant boundary isolation (`organization_id`).
  - Accessible only to the landholder and authorized field dispatchers.

### Tier 2: Operational & Commercial Fleet Data (Internal / Business Confidential)
- **Data Elements:** Mobile bio-refinery unit telematics, 2-opt sequenced route collection stops, weighbridge harvest yields, techno-economic cash flow models, commercial briquette/biochar sales invoices.
- **Protection Controls:**
  - Role-based authorization (`FIELD_OPERATOR`, `ORGANIZATION_MANAGER`).
  - Encrypted in transit (TLS 1.3) and at rest (AES-256).
  - Row-level tenant partitioning.

### Tier 3: Scientific & Earth Observation Data (Public / Open Access)
- **Data Elements:** NASA FIRMS MODIS (Terra/Aqua) and VIIRS (Suomi-NPP/NOAA-20) active fire hot spots, harmonized fire radiative power (FRP), historical multi-year burning baselines, PAU/ICAR crop calendars, ESA Copernicus 10m Land Use Land Cover (LULC) maps.
- **Protection Controls:**
  - Readily accessible to public visitors, environmental researchers, and state regulators.
  - Immutable provenance metadata linking observations to official satellite sources.

### Tier 4: Security & Governance Data (Restricted / Privileged)
- **Data Elements:** PBKDF2-SHA256 password hashes, HMAC-SHA256 JWT signing keys, system encryption secrets, append-only `AuditLog` records, `SecurityEvent` anomaly detections.
- **Protection Controls:**
  - Access strictly restricted to `SYSTEM_ADMINISTRATOR`.
  - Zero plaintext storage of passwords or tokens.
  - Append-only database constraints.

---

## 3. Statutory Data Retention Schedules

Pursuant to Section 8(7) of the DPDP Act 2023, personal data and operational records are retained only for as long as necessary to satisfy the purpose for which they were collected or statutory compliance mandates.

| Data Category | Retention Period | Action on Expiry | Statutory Legal Basis |
| :--- | :--- | :--- | :--- |
| **`AUDIT_LOGS`** | 730 Days (2 Years) | Archive / Read-Only Cold Storage | Companies Act 2013, IT Act 2000, Section 8(7) DPDP Act 2023 |
| **`USER_SESSIONS`** | 30 Days | Hard Delete (Purge) | Zero-trust session lifecycle hygiene |
| **`INACTIVE_USERS`** | 1095 Days (3 Years) | Anonymize / Soft Delete | DPDP Act 2023 Right to Erasure & Purpose Limitation |
| **`FARM_COORDINATES`** | Active Contract + 1 Year | Obfuscate to 2 Decimals | Agricultural tenancy and cooperative membership lifecycle |
| **`LCA_ASSESSMENTS`** | 3650 Days (10 Years) | Retain for MRV Audits | Verra VM0044 & Puro.earth carbon credit registry verification |

---

## 4. Enforcement Automation
The platform provides a statutory retention compliance sweep via `DataRetentionPolicy`:
- Triggerable via administrative API or scheduled cron tasks.
- Verifies that expired sessions are purged and inactive personal identifiers are anonymized.
