# Stubble2Power - Security Incident Response Protocol

## 1. Purpose and Scope
This document outlines the standard operational protocol for detecting, containing, investigating, and remediating security incidents across the Stubble2Power platform. It applies to all infrastructure, APIs, databases, tenant workspaces, and personal data processed under the Digital Personal Data Protection (DPDP) Act 2023.

---

## 2. Incident Classification Matrix

| Severity Level | Definition | Impact Examples | Response SLA |
| :--- | :--- | :--- | :--- |
| **P1 - Critical** | Catastrophic incident compromising system integrity, widespread data breach, or administrative credential compromise. | - Unauthorized dump of farmer parcel coordinates and Aadhaar hashes.<br>- Arbitrary code execution on backend host.<br>- Compromise of master JWT signing secret. | Triage: < 15 min<br>Containment: < 1 hour |
| **P2 - High** | Significant breach of tenant isolation or unauthorized modification of operational / financial data. | - Cross-tenant data access (IDOR between cooperatives).<br>- Unauthorized modification of configuration parameters or carbon credit formulas. | Triage: < 30 min<br>Containment: < 4 hours |
| **P3 - Medium** | Limited security anomalies or localized service degradation. | - Repeated brute force login attempts on single user account.<br>- Suspicious export volume of public satellite data. | Triage: < 2 hours<br>Containment: < 12 hours |
| **P4 - Low** | Minor policy violation or benign security scanner activity. | - Single failed login from unusual IP address.<br>- Minor schema validation discrepancy. | Triage: < 8 hours<br>Remediation: Next sprint |

---

## 3. Incident Lifecycle Phases

```
+------------------+     +--------------------+     +------------------+
|  1. Detection    | --> |   2. Containment   | --> |  3. Eradication  |
|   and Triage     |     |   and Isolation    |     |  and Patching    |
+------------------+     +--------------------+     +------------------+
                                                              |
+------------------+     +--------------------+               v
| 5. Post-Mortem   | <-- |   4. Recovery and  | <-------------+
| and DPDP Report  |     |     Verification   |
+------------------+     +--------------------+
```

### Phase 1: Detection and Triage
- **Automated Detection:** Security events logged in `SecurityEvent` table (e.g., `LOGIN_FAILURE`, `UNAUTHORIZED_ACCESS`, `RATE_LIMIT_EXCEEDED`).
- **Audit Monitoring:** Administrative reviews of `AuditLog` for unusual query spikes or unauthorized state changes.
- **Triage Checklist:**
  1. Determine affected resource IDs, tenant organizations, and user accounts.
  2. Assign Incident Commander (Lead Security Engineer).
  3. Classify incident severity (P1-P4).

### Phase 2: Containment and Isolation
- **Emergency Session Revocation:** If an active token or user account is compromised, execute session invalidation:
  ```python
  from backend.models.database import SessionLocal
  from backend.models.entities import UserSession, User

  db = SessionLocal()
  # Invalidate all active sessions for compromised user
  db.query(UserSession).filter(UserSession.user_id == compromised_user_id).update({"is_revoked": True})
  # Deactivate user account
  db.query(User).filter(User.id == compromised_user_id).update({"is_active": False})
  db.commit()
  ```
- **JWT Secret Key Rotation:** If the system secret is compromised:
  1. Update `security.jwt_secret` in environment / configuration registry.
  2. All existing JWT access and refresh tokens will be immediately invalidated by the HMAC verifier.
- **Network Isolation:** Apply firewall ingress drops to malicious IPs identified in `client_ip`.

### Phase 3: Eradication
- Identify and patch root-cause vulnerability (e.g., missing authorization check, flawed regex, insecure dependency).
- Verify database state against append-only `AuditLog` to rollback any unauthorized mutations.

### Phase 4: Recovery and Verification
- Re-enable services in staging, run full automated test suite (`pytest`), verify tenant boundary isolation.
- Restore patched services to production with heightened audit logging enabled.

### Phase 5: Post-Mortem and Statutory DPDP Notification
- **Statutory Regulatory Disclosure:** Under Section 8(6) of the Digital Personal Data Protection Act 2023, in the event of a personal data breach, the platform Data Protection Officer (DPO) MUST notify:
  1. The **Data Protection Board of India (DPBI)** within the statutorily prescribed timeframe.
  2. Each affected **Data Principal (Farmer / Landholder)** in clear, plain language detailing the nature of the breach, affected data categories, and mitigation steps taken.
- **Post-Incident Review Dossier:** Document root cause, timeline of events, mean time to detect (MTTD), mean time to contain (MTTC), and preventative architectural modifications.
