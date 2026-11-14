# Stubble2Power - Identity & Authentication Architecture

## 1. Overview
Stubble2Power implements a cryptographic, stateless, multi-tenant identity and authentication system designed for zero-trust environments. The system supports web sessions, field mobile clients, and REST API consumers with fine-grained role claims.

---

## 2. Password Security Architecture
All user passwords are encrypted and verified using **PBKDF2-SHA256** (Password-Based Key Derivation Function 2) with a cryptographic salt:
- **Hashing Algorithm:** PBKDF2 with SHA-256 pseudorandom function.
- **Iteration Count:** 100,000 iterations (OWASP 2026 recommended baseline).
- **Implementation:** Powered by the industry-standard `passlib` cryptography library.
- **Zero Plaintext Storage:** Passwords are never logged, stored in cache, or returned in API responses.

```python
from backend.core.security.password import hash_password, verify_password

# Registration / Password Change
hashed = hash_password(plaintext_password)

# Authentication Verification
is_valid = verify_password(plaintext_password, hashed)
```

---

## 3. JWT Token Governance & Claims

Authentication produces JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).

### 3.1 Token Types
1. **Access Token:** Short-lived (default 60 minutes) token authorizing API operations.
2. **Refresh Token:** Long-lived (default 7 days) token used exclusively to reissue access tokens without re-prompting for credentials.

### 3.2 JWT Payload Claims Structure
```json
{
  "sub": "4",
  "username": "analyst_priya",
  "role": "AGRICULTURAL_ANALYST",
  "organization_id": 1,
  "farmer_id": null,
  "token_type": "access",
  "iat": 1797331200,
  "exp": 1797334800
}
```

### 3.3 Epoch Timestamp Synchronization
To eliminate issues with naive UTC vs local system timezones (such as Indian Standard Time UTC+5:30), all token generation uses standardized UNIX epoch integers (`int(time.time())`).

---

## 4. Session Tracking & Instant Revocation
While JWTs are stateless by design, Stubble2Power provides an active session table (`UserSession`) to support instant session revocation:
1. When an access token is issued, its SHA-256 fingerprint is recorded in `user_sessions`.
2. When a user logs out or an account is compromised, the corresponding session is flagged `is_revoked = True`.
3. High-security operations verify that the incoming token's hash is not present in the revoked session registry.

---

## 5. Pre-Seeded Benchmark Identity Profiles

To facilitate immediate verification and multi-role testing, the following benchmark accounts are seeded:

| Username | Role | Tenant Organization | Purpose |
| :--- | :--- | :--- | :--- |
| `public_visitor` | `PUBLIC_VISITOR` | PUBLIC | Guest access, obfuscated satellite fire views. |
| `gurpreet_singh` | `FARMER` | PB-BIO-COOP (ID: 1) | Landholder portal, parcel maps, harvest logs, DPDP consent. |
| `operator_ramesh` | `FIELD_OPERATOR` | PB-BIO-COOP (ID: 1) | Mobile refinery dispatch, 2-opt route stops, status updater. |
| `analyst_priya` | `AGRICULTURAL_ANALYST` | PB-BIO-COOP (ID: 1) | PAU crop calendars, LULC cropland checks, biomass analytics. |
| `analyst_vikram` | `ENVIRONMENTAL_ANALYST` | MAPS-MALWA (ID: 2) | FIRMS harmonization, anomaly detection, LCA carbon credits. |
| `manager_harpreet`| `ORGANIZATION_MANAGER` | PB-BIO-COOP (ID: 1) | Cooperative portfolio, fleet planner, techno-economic DCF. |
| `admin` | `SYSTEM_ADMINISTRATOR` | SYSTEM (Global) | RBAC management, dynamic config registry, audit logs. |
