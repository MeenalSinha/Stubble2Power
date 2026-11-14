# Stubble2Power - Multi-Tenant Organization Isolation Architecture

## 1. Overview
Stubble2Power employs a robust multi-tenant architecture designed to support diverse agricultural entities—including farmer producer cooperatives (FPOs), private biomass aggregators, clean-energy utilities, and state agricultural departments—on a shared, highly scalable infrastructure.

---

## 2. Multi-Tenancy Design Pattern

### 2.1 Shared Database, Row-Level Discriminant Model
Stubble2Power adopts a **shared database, row-level tenant isolation pattern** with foreign key indexing on `organization_id`:
- **Efficiency:** Single database schema eliminates the overhead of managing hundreds of individual database instances.
- **Tenant Scope:** Each core operational entity includes an explicit, indexed `organization_id` foreign key:
  - `Farmer.organization_id`
  - `Farm.organization_id`
  - `MobileBioRefinery.organization_id`
  - `DeploymentPlan.organization_id`
  - `FinancialScenario.organization_id`
  - `EnvironmentalAssessment.organization_id`
  - `SavedReport.organization_id`
  - `User.organization_id`

---

## 3. Strict Cross-Tenant Denial Rules

1. **Automatic Query Filtering:**
   All read and search operations executed by non-admin users automatically filter by `organization_id`:
   ```python
   def get_farmers_for_user(db: Session, current_user: User):
       if current_user.role_name == RoleName.SYSTEM_ADMINISTRATOR.value:
           return db.query(Farmer).all()
       return db.query(Farmer).filter(Farmer.organization_id == current_user.organization_id).all()
   ```

2. **Cross-Tenant Mutation Denial (HTTP 403 Forbidden):**
   If an authenticated manager from Organization 1 (`PB-BIO-COOP`) attempts to modify or assign resources belonging to Organization 2 (`MAPS-MALWA`), the backend dependency `verify_organization_access` terminates the request and raises `AuthorizationError`:
   ```python
   def verify_organization_access(user: User, target_organization_id: int):
       if user.role_name == RoleName.SYSTEM_ADMINISTRATOR.value:
           return True
       if user.organization_id != target_organization_id:
           raise AuthorizationError("Access denied: Target resource belongs to a different tenant organization.")
       return True
   ```

3. **Global Administrative Audit Logging:**
   When a `SYSTEM_ADMINISTRATOR` accesses or modifies resources across tenant boundaries, an explicit record is logged to the `AuditLog` table capturing the actor, target organization, action, and rationale.

---

## 4. Tenant Membership Model

The platform supports multi-tenant affiliations through the `OrganizationMembership` model:
- Users can have primary affiliations (`User.organization_id`) or secondary multi-tenant roles (`OrganizationMembership`).
- Membership records specify the user's role within that specific cooperative, whether the membership is active, and the grant timestamp.

---

## 5. Security Verification
Multi-tenant isolation rules are covered by automated integration tests in `tests/integration/test_phase13_14_api.py`, confirming:
- Tenant A cannot retrieve Tenant B's farmers.
- Tenant A cannot modify Tenant B's deployment plans.
- System administrators can administer all tenant domains with audit verification.
