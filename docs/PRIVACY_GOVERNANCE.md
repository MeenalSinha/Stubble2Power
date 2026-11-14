# Stubble2Power - Privacy Governance & DPDP Act 2023 Compliance

## 1. Statutory Framework
The Stubble2Power platform processes agricultural landholder information in strict alignment with India's **Digital Personal Data Protection (DPDP) Act 2023**. This document outlines the technical and legal controls governing personal data handling, consent life cycles, data subject rights, and geospatial location obfuscation.

---

## 2. Purpose-Bound Consent Architecture

Under Section 6 of the DPDP Act 2023, personal data may only be processed for specific, lawful purposes explicitly consented to by the Data Principal (Farmer).

### 2.1 Standardized Processing Purposes
1. **`BIOMASS_AGGREGATION`:** Processing farm parcel acreage, soil types, and crop cultivation data to estimate stubble residue volume.
2. **`SATELLITE_FIRE_CORRELATION`:** Correlating NASA MODIS/VIIRS Earth Observation hot spots with farm parcel locations for fire avoidance verification.
3. **`LOGISTICS_DISPATCH`:** Sharing exact parcel coordinates and contact details with mobile bio-refinery operators for scheduled stubble baling.
4. **`DIRECT_PAYMENT`:** Processing bank account and Aadhaar details for disbursement of biomass procurement payments.

### 2.2 Consent Record Entity (`ConsentRecord`)
Each consent event is recorded in an immutable, auditable log capturing:
- `farmer_id` and `user_id`
- `consent_purpose`
- `consent_version` (e.g., `v1.0`)
- `is_granted` (Boolean status)
- `consent_timestamp`
- `withdrawn_at` (Timestamp of withdrawal)
- `ip_address` and `notes`

### 2.3 Real-Time Consent Withdrawal
Farmers have the statutory right to withdraw consent at any time via the Farmer Workspace UI or API (`/api/privacy/consent/withdraw`).
- Upon withdrawal, the status is immediately updated in the database.
- Subsequent dispatch routes and aggregation models exclude withdrawn parcels from processing.

---

## 3. Data Subject Rights (DSR) Implementation

Under Chapter III of the DPDP Act 2023, Data Principals are afforded specific rights managed through the `DataSubjectRequest` entity:

1. **Right to Access (`ACCESS`):** Farmers can request a summary of all personal data held by the platform, including cultivation records, coordinates, and payout history.
2. **Right to Correction / Rectification (`CORRECTION`):** Farmers can submit requests to update out-of-date personal details, bank accounts, or acreage.
3. **Right to Erasure (`ERASURE`):** Farmers can request the deletion of their personal records upon terminating cooperative membership, subject to statutory retention limits.
4. **Right to Data Portability / Export (`EXPORT`):** Farmers can download an auditable, machine-readable statement (CSV/JSON) of their historical yields, biomass deliveries, and payments.

### 3.1 DSR Request Workflow
```
[Farmer Submits DSR via UI/API]
               |
               v
      [Status: SUBMITTED]
               |
               v
  [Privacy Officer / Admin Reviews] --> [Status: IN_REVIEW]
               |
               v
[Action Executed: Data Exported / Updated / Purged]
               |
               v
      [Status: COMPLETED]
```

---

## 4. Geospatial Location Obfuscation Filter

Directly exposing farm parcel coordinates on public satellite fire intelligence maps compromises farmer property privacy and risks unfair stigmatization.

### 4.1 2-Decimal Obfuscation Algorithm
The platform applies an automated privacy filter to coordinates displayed on public interfaces:
- **Public Visitor Resolution:** Latitude and longitude are rounded to 2 decimal places ($\approx 1.1\text{ km}$ at $30^\circ\text{N}$ latitude).
- **Owner / Dispatcher Resolution:** Enrolled parcel owners and authorized mobile refinery dispatchers view exact 4-decimal place coordinates ($\approx 11\text{ meters}$) to ensure precise field logistics.

```python
def obfuscate_coordinates(record, decimal_places=2):
    return {
        "latitude": round(record.latitude, decimal_places),
        "longitude": round(record.longitude, decimal_places),
        "is_obfuscated": True,
        "resolution_km": 1.11
    }
```

---

## 5. Data Protection Officer (DPO) Contact
In accordance with DPDP Act 2023 requirements, queries regarding personal data handling, grievances, or statutory requests can be directed to the designated Data Protection Officer at:
- **Email:** `privacy@stubble2power.org`
- **Grievance Redressal SLA:** Acknowledgment within 24 hours; resolution within 7 working days.
