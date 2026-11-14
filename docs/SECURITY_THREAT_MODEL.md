# Stubble2Power - Security Threat Model (STRIDE Methodology)

## 1. Executive Summary
Stubble2Power is an enterprise-grade agricultural intelligence and decentralized clean-energy operations platform. Because the platform processes sensitive landholder personal data (under the Digital Personal Data Protection Act 2023), operational dispatch routes, financial cash flows, and NASA Earth Observation datasets, robust threat modeling is essential.

This document identifies core platform assets, threat actor profiles, attack surfaces, and analyzes risks using Microsoft's **STRIDE** methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

---

## 2. Platform Assets and Trust Boundaries

### 2.1 Critical Information Assets
1. **Farmer Digital Identity & Personal Data (PII):** Full names, masked Aadhaar numbers, phone numbers, spatial parcel boundaries.
2. **Operational Fleet Logistics & Route Plans:** Mobile bio-refinery current coordinates, sequenced farm collection schedules, vehicle drivers.
3. **Financial Feasibility & Cash Settlement Records:** Direct farmer procurement payments, bank accounts, briquette/biochar sales invoices, carbon credit registries.
4. **NASA Earth Observation & Ingestion Credentials:** NASA Earthdata MAP_KEY, API tokens, FIRMS raw and harmonized hot spot data.
5. **System Domain Configuration Parameters:** Scientific RPR ratios, emissions factors, CAPEX/OPEX settings in `ConfigManager`.
6. **Immutable Audit Trail:** Append-only security events and audit records.

### 2.2 Trust Boundaries
- **Trust Boundary 1: Public Internet / Public Visitor:** Unauthenticated or anonymous users accessing the public web application and public API endpoints.
- **Trust Boundary 2: Authenticated Landholders & Operators:** Authenticated users accessing scoped tenant resources with JWT bearer tokens.
- **Trust Boundary 3: Tenant Organizations:** Boundaries separating Cooperative A (`PB-BIO-COOP`) from Private Aggregator B (`MAPS-MALWA`).
- **Trust Boundary 4: Application Server to Database / Object Store:** Backend FastAPI runtime to PostgreSQL/PostGIS database and local/GCS storage.

---

## 3. Threat Actor Taxonomy
1. **Curious / Opportunistic Attackers:** Automated web scanners, unauthenticated external visitors attempting injection attacks or scraping private farm locations.
2. **Rival Aggregators / Malicious Competitors:** External parties attempting to access competitor farmer registries, yield estimates, or route plans to intercept biomass.
3. **Malicious Insider / Rogue Tenant Member:** Authenticated users attempting Insecure Direct Object Reference (IDOR) attacks to access cross-tenant records or escalate privileges.
4. **Compromised Field Device:** A tablet or mobile device belonging to a field operator seized or infected with malware.

---

## 4. STRIDE Threat Analysis and Mitigations

| Threat Category | Potential Attack Vector | Impact | Platform Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Spoofing (Identity)** | Adversary guesses user credentials or creates forged JWT bearer tokens to impersonate administrators or farmers. | Unauthorized access to tenant databases and administrative settings. | - Password hashing using salted PBKDF2-SHA256 with 100,000 iterations.<br>- HMAC-SHA256 JWT tokens with 60-minute expiry.<br>- Token hashing (SHA-256) stored in `UserSession` to allow instant revocation.<br>- Rejection of expired tokens (`int(time.time())` epoch standardization). |
| **Tampering (Data Integrity)** | Adversary alters biomass harvest records, adjusts carbon credit formulas, or manipulates configuration parameters. | Inflated payouts, fraudulent carbon credits, incorrect fleet routing. | - Strict schema validation via Pydantic v2.<br>- Role-Based Access Control (`SYSTEM_ADMINISTRATOR` required for `config:update`).<br>- Real-time provenance tracking on all configuration changes.<br>- Transactional database integrity constraints. |
| **Repudiation** | User denies updating a route stop, modifying biomass yields, or withdrawing DPDP consent. | Inability to audit unauthorized operations or settle disputes. | - Immutable `AuditLog` table capturing timestamp, actor ID, action, resource type, IP, and status.<br>- Append-only `ConsentRecord` table logging grant/withdrawal timestamps and purpose. |
| **Information Disclosure** | External actor scrapes public satellite maps to pinpoint precise farmer parcel boundaries; cross-tenant data leakage. | Breach of DPDP Act 2023; loss of farmer trust and regulatory fines. | - Automatic geospatial location obfuscation (coordinates truncated to 2 decimal places / ~1.1 km resolution for public visitors).<br>- Strict tenant filtering (`organization_id` checks on all DB queries).<br>- Masking of sensitive fields (Aadhaar numbers masked as `XXXX-XXXX-1234`). |
| **Denial of Service** | Volumetric HTTP flooding of NASA ingestion or LCA calculation endpoints. | Server exhaustion, blocking field operations during peak harvest. | - Configurable rate limiting (`security.api_rate_limit_per_minute: 120`).<br>- Asynchronous background tasks for resource-intensive operations.<br>- Local caching of NASA observation files. |
| **Elevation of Privilege** | Farmer or Field Operator alters request payload to invoke admin or manager APIs (IDOR). | Unauthorized modification of fleet plans or user roles. | - Centralized FastAPI RBAC dependencies (`require_permission`, `require_role`).<br>- Server-side resource ownership verification (`verify_resource_ownership`).<br>- Zero client-side trust. |

---

## 5. Security Architecture Verification
- **Automated Security Test Suite:** Evaluated in `tests/unit/test_phase14_security_rbac.py` and `tests/integration/test_phase13_14_api.py`.
- **Zero Hardcoded Credentials:** All secrets sourced from environment variables and dynamically managed through `config_manager`.
