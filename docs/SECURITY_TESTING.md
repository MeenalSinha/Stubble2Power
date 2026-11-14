# Stubble2Power - Security & Governance Automated Test Suite

## 1. Overview
Stubble2Power integrates a comprehensive automated security testing suite verifying cryptography, JWT tokens, Role-Based Access Control (RBAC), multi-tenant isolation, location privacy, DPDP Act 2023 consent lifecycles, and user experience services.

---

## 2. Test Suite Architecture & Coverage

The automated security and governance test suite comprises **18 dedicated test cases** across unit and integration tiers, contributing to the platform's **101 total automated tests**:

```
tests/
├── unit/
│   ├── test_phase14_security_rbac.py   (8 test cases - Cryptography, RBAC, Privacy)
│   └── test_phase13_ux.py              (4 test cases - i18n, Preferences, Notifications, Reports)
└── integration/
    └── test_phase13_14_api.py          (6 test cases - Auth, RBAC Enforcement, Multi-Tenancy, DSR)
```

---

## 3. Detailed Test Catalog

### 3.1 Unit Tier: Security & RBAC (`test_phase14_security_rbac.py`)
1. **`test_password_hashing_and_verification`:** Verifies salted PBKDF2-SHA256 password hashing with 100,000 rounds. Validates that correct passwords pass and altered passwords fail.
2. **`test_jwt_token_creation_and_decoding`:** Validates HMAC-SHA256 JWT access and refresh token issuance, standardized epoch timestamps, and claim decoding.
3. **`test_jwt_token_expiration`:** Confirms that expired tokens trigger `ExpiredSignatureError` and are rejected by authorization handlers.
4. **`test_rbac_permissions_matrix`:** Validates that all 7 platform roles possess exact, expected granular permissions and denies unauthorized permission lookups.
5. **`test_object_level_authorization_and_tenant_isolation`:** Verifies that farmers can only access their own parcel IDs and managers can only access their own tenant organization.
6. **`test_location_privacy_obfuscation`:** Validates that public visitors receive coordinates blurred to 2 decimal places ($\approx 1.1\text{ km}$), while authorized owners view exact coordinates.
7. **`test_dpdp_purpose_bound_consent`:** Validates that consent granting, status inspection, and withdrawal function with real-time effect.
8. **`test_data_subject_request_workflow`:** Validates the submission and lifecycle progression of statutory DPDP Data Subject Requests.

### 3.2 Unit Tier: User Experience (`test_phase13_ux.py`)
1. **`test_i18n_localization_coverage`:** Confirms dictionary completeness for English, Hindi, and Punjabi across core platform labels.
2. **`test_user_preferences_service`:** Validates storage and updating of user UI preferences (preferred language, default AOI, theme).
3. **`test_notification_service`:** Tests creation, priority classification, filtering, and mark-as-read status for in-app user notifications.
4. **`test_saved_reports_service`:** Verifies generation and auditable retrieval of serialized report dossiers.

### 3.3 Integration Tier: Security & Governance APIs (`test_phase13_14_api.py`)
1. **`test_auth_registration_and_login_flow`:** End-to-end API test covering user registration, password verification, and JWT session generation.
2. **`test_rbac_permission_enforcement_on_endpoints`:** Verifies HTTP 403 Forbidden denial when a `FARMER` attempts to call administrative user management endpoints.
3. **`test_cross_tenant_organization_isolation_enforcement`:** Validates that a manager belonging to Tenant A is denied access to Tenant B's farmer registry.
4. **`test_privacy_consent_and_audit_api`:** Verifies API routes for recording purpose-bound consent and submitting Data Subject Requests.
5. **`test_configuration_registry_update_with_audit`:** Verifies that administrative updates to configuration parameters update the database and write an immutable audit log.
6. **`test_location_obfuscation_api`:** Verifies that the public API endpoint returns blurred coordinates for unauthenticated queries.

---

## 4. Execution Command & Benchmark Output
```bash
pytest tests/unit/test_phase14_security_rbac.py tests/unit/test_phase13_ux.py tests/integration/test_phase13_14_api.py
```

### Benchmark Results:
```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-8.2.2, pluggy-1.6.0
rootdir: C:\Users\Meenal Sinha\Downloads\Stubble2Power
configfile: pytest.ini
plugins: anyio-4.12.0, asyncio-0.23.7, cov-7.1.0, mock-3.16.0
asyncio: mode=Mode.STRICT
collected 18 items

tests\unit\test_phase14_security_rbac.py ........                        [ 44%]
tests\unit\test_phase13_ux.py ....                                       [ 66%]
tests\integration\test_phase13_14_api.py ......                          [100%]

============================= 18 passed in 3.07s ==============================
```
- **Total Test Suite Pass Rate:** 101/101 tests passed (100%).
