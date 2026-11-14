# Stubble2Power — Production Operational Handover

**Document ID:** S2P-DOC-OPS-HAN-2026-V1  
**Classification:** Operational Handover & SLA Governance  
**Platform Version:** v2.5.0  

---

## 1. Handover Scope & System Summary

Stubble2Power v2.5.0 is formally handed over to the Site Reliability Engineering (SRE), DevOps, and Production Operations teams.

The platform comprises:
- **FastAPI Backend Service:** High-performance asynchronous REST API running under Uvicorn with 4 worker processes.
- **Streamlit Frontend Dashboard:** Multi-workspace interactive application with glassmorphism design system and multilingual localization (English, Hindi, Punjabi).
- **PostGIS Relational Database:** Spatial PostgreSQL 16 database running PostGIS 3.4 extensions.
- **Automated Backup & Restore Subsystem:** Python utilities supporting SQLite and PostgreSQL with streaming cryptographic SHA-256 validation.

---

## 2. Service Level Agreements (SLAs)

### 2.1 Target Availability
- **Overall System Availability:** $99.9\%$ monthly uptime (excluding scheduled maintenance windows announced $\ge 48\text{ hours}$ in advance).
- **Scheduled Maintenance Window:** Sunday 01:00 UTC to 03:00 UTC.

### 2.2 Incident Severity & Response Matrix

| Severity Level | Definition | Max Initial Response Time | Target Resolution Time | Escalation Path |
|:---|:---|:---:|:---:|:---|
| **P1 - Critical** | Platform entirely down; database unavailable; data corruption; security breach. | $< 15\text{ minutes}$ | $< 2\text{ hours}$ | Lead SRE $\rightarrow$ DevOps Architect $\rightarrow$ Security Officer |
| **P2 - High** | Satellite ingestion pipeline halted; route planning failing; core analytical engine down. | $< 1\text{ hour}$ | $< 6\text{ hours}$ | On-Call Engineer $\rightarrow$ Backend Lead |
| **P3 - Medium** | Non-critical UI glitch; minor API latency spike; single report generation delayed. | $< 4\text{ hours}$ | $< 24\text{ hours}$ | Application Support Engineer |
| **P4 - Low** | Minor cosmetic defect; documentation request; non-urgent parameter change. | $< 24\text{ hours}$ | Next Sprint Release | Product Backlog |

---

## 3. Operations Contact Registry & Escalation Matrix

| Role | Title / Designation | Responsibility | Coverage |
|:---|:---|:---|:---:|
| **Primary On-Call SRE** | Site Reliability Engineer | Container health, host metrics, database alerts | 24/7 PagerDuty |
| **Secondary SRE** | DevOps Specialist | Cloud infrastructure, network routing, backups | 24/7 Escalation |
| **Database Administrator** | Database Architect | PostGIS tuning, replication, index maintenance | Business Hours |
| **Application Security Officer**| Lead Security Engineer | Threat management, vulnerability patching, DPDP audits | On-Call for P1 |
| **Principal Architect** | Product Technical Lead | Architecture decisions, root cause review | Escalation |

---

## 4. Health Probes & Monitoring Metrics

### 4.1 Automated Healthcheck Endpoints
- **Backend Health:** `GET http://localhost:8000/api/v1/health`
  - Validates database connectivity, NASA FIRMS status, and configuration integrity.
  - Expected HTTP Status: `200 OK`.
- **Frontend Health:** `GET http://localhost:8501/_stcore/health`
  - Validates Streamlit server readiness.
  - Expected HTTP Status: `200 OK`.
- **Database Readiness:** `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}`
  - Validates PostgreSQL socket and client connections.

### 4.2 Key Telemetry Metrics & Alerting Thresholds
- **HTTP 5xx Error Rate:** Alert when $5\text{xx} \ge 1.0\%$ over 5-minute rolling window.
- **API Latency (p95):** Alert when $p95 \ge 500\text{ ms}$ for standard endpoints; $p95 \ge 2000\text{ ms}$ for 2-Opt route solving.
- **Database Connection Pool Exhaustion:** Alert when active connections reach $85\%$ of `max_connections`.
- **Disk Utilization:** Alert when persistent volume `postgres_prod_data` reaches $\ge 80\%$ capacity.
- **CPU / Memory Limits:** Alert if container memory approaches $\ge 90\%$ of allocated cgroup limit ($2048\text{ MB}$ backend, $4096\text{ MB}$ db).

---

## 5. Routine Maintenance & Operational Schedule

| Cadence | Task Description | Executed By | Validation Procedure |
|:---|:---|:---:|:---|
| **Daily (02:00 UTC)** | Automated database backup and SHA-256 verification. | `scripts/backup_db.py` cron | Verify exit code 0 and presence of `.dump` and `.sha256` files. |
| **Weekly (Sunday 03:00 UTC)** | Automated data retention sweep. | SRE Cron | Run DPDP retention policy to purge expired sessions (>30 days). |
| **Monthly** | Off-site disaster recovery restoration test. | SRE Team | Run `scripts/restore_db.py` in test environment and verify smoke tests. |
| **Quarterly** | NASA FIRMS MAP Key validation & quota review. | Operations | Verify API consumption rates and renewal dates. |
| **Biannual** | Dependency security vulnerability scan (`pip-audit`, `bandit`). | Security Team | Review CVE reports and patch base container images. |

---

## 6. Emergency Recovery & Incident Playbook

### 6.1 Database Unavailability Incident
1. Check container status:
   ```bash
   docker compose -f docker-compose.prod.yml ps db
   ```
2. Inspect database logs for out-of-memory (OOM) or storage exhaustion:
   ```bash
   docker logs --tail 100 stubble2power-prod-db
   ```
3. If volume corruption is suspected, initiate emergency restoration from the latest verified backup:
   ```bash
   python scripts/restore_db.py /var/backups/stubble2power/LATEST_BACKUP.dump
   ```

### 6.2 Application Rolling Restart
If backend workers become unresponsive:
```bash
docker compose -f docker-compose.prod.yml restart backend
```

---

## 7. Sign-off & Acceptance
This operational handover document confirms that Stubble2Power v2.5.0 satisfies all stability, observability, disaster recovery, and operational criteria required for 24/7 enterprise production service.
