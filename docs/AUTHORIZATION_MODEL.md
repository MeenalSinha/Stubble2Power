# Stubble2Power - Role-Based Authorization Model (RBAC)

## 1. Overview
Stubble2Power enforces strict server-side **Role-Based Access Control (RBAC)** paired with **Object-Level Authorization** to guarantee least-privilege security and prevent Insecure Direct Object References (IDOR). Authorization logic is enforced in backend API dependency chains and database repositories.

---

## 2. Seven Standard Platform Roles

1. **`PUBLIC_VISITOR`:** Unauthenticated guest or general public user. Access is restricted to public satellite fire maps (with 2-decimal location obfuscation), historical activity calendars, and educational content.
2. **`FARMER`:** Verified agricultural landholder. Can view their own exact farm parcels, log grain harvests, view biomass availability, manage DPDP statutory consents, submit data subject requests, and view settlement statements.
3. **`FIELD_OPERATOR`:** Mobile bio-refinery operator or logistics driver. Authorized to view assigned equipment, execute 2-opt collection routes, update sequenced farm stop statuses (`PENDING`, `IN_TRANSIT`, `ARRIVED`, `PICKED_UP`, `PROCESSED`), and monitor transit fuel KPIs.
4. **`AGRICULTURAL_ANALYST`:** Agronomist or supply chain planner. Accesses PAU/ICAR crop calendars, ESA WorldCover cropland verification masks, regional biomass availability statistics, and exports agricultural reports.
5. **`ENVIRONMENTAL_ANALYST`:** Remote sensing specialist or carbon accounting auditor. Accesses NASA FIRMS satellite data, cross-sensor harmonization engines, seasonal fire anomaly detection, and calculates cradle-to-grave LCA net emissions and carbon credits.
6. **`ORGANIZATION_MANAGER`:** Cooperative administrator or agribusiness executive. Manages cooperative farmer portfolios, runs multi-unit mobile refinery deployment planners, conducts techno-economic DCF feasibility simulations, and exports cooperative dossiers.
7. **`SYSTEM_ADMINISTRATOR`:** Global platform administrator. Manages user accounts, configures tenant organizations, dynamically edits configuration registry parameters with automated provenance tracking, audits immutable system logs, and enforces statutory data retention policies.

---

## 3. Granular RBAC Permissions Matrix

| Granular Permission | Public Visitor | Farmer | Field Operator | Agri Analyst | Env Analyst | Org Manager | Sys Admin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `public:read_satellite` | YES | YES | YES | YES | YES | YES | YES |
| `farmers:read_own` | NO | YES | NO | NO | NO | NO | YES |
| `farmers:read_org` | NO | NO | YES | YES | NO | YES | YES |
| `farms:create` | NO | YES | NO | NO | NO | YES | YES |
| `farms:read_exact` | NO | YES | YES | YES | YES | YES | YES |
| `harvest:log` | NO | YES | NO | NO | NO | YES | YES |
| `biomass:read` | NO | YES | YES | YES | YES | YES | YES |
| `biomass:estimate` | NO | YES | NO | YES | NO | YES | YES |
| `fleet:view` | NO | NO | YES | NO | NO | YES | YES |
| `routes:view_assigned`| NO | NO | YES | NO | NO | YES | YES |
| `routes:update_status`| NO | NO | YES | NO | NO | NO | YES |
| `agri:crop_calendar` | NO | NO | NO | YES | NO | YES | YES |
| `agri:land_use` | NO | NO | NO | YES | NO | YES | YES |
| `env:nasa_firms` | NO | NO | NO | NO | YES | YES | YES |
| `env:harmonization` | NO | NO | NO | NO | YES | YES | YES |
| `env:anomalies` | NO | NO | NO | NO | YES | YES | YES |
| `env:lca_calculate` | NO | NO | NO | NO | YES | YES | YES |
| `org:manage_portfolio`| NO | NO | NO | NO | NO | YES | YES |
| `fleet:plan_deployment`| NO | NO | NO | NO | NO | YES | YES |
| `econ:dcf_simulate` | NO | NO | NO | NO | NO | YES | YES |
| `privacy:manage_consent`| NO | YES | NO | NO | NO | NO | YES |
| `privacy:submit_dsr` | NO | YES | YES | YES | YES | YES | YES |
| `config:read` | NO | NO | NO | YES | YES | YES | YES |
| `config:update` | NO | NO | NO | NO | NO | NO | YES |
| `admin:users` | NO | NO | NO | NO | NO | NO | YES |
| `admin:organizations`| NO | NO | NO | NO | NO | NO | YES |
| `admin:audit_logs` | NO | NO | NO | NO | NO | NO | YES |

---

## 4. Server-Side Enforcement Mechanisms

### 4.1 Permission Check Dependency
```python
from backend.api.dependencies.auth import require_permission
from backend.core.security.rbac import PermissionName

@router.post("/harvest/log")
def log_harvest(
    payload: HarvestLogCreate,
    current_user: User = Depends(require_permission(PermissionName.HARVEST_LOG))
):
    ...
```

### 4.2 Object-Level IDOR Prevention
```python
from backend.api.dependencies.auth import verify_resource_ownership

# Validates that a Farmer can only access parcels they own
verify_resource_ownership(current_user, target_farmer_id=farm.farmer_id)
```
