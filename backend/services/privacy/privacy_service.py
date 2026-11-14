"""
Data Privacy, Consent & Subject Rights Governance Service.
Implements DPDP Act 2023, ISO 27701 consent management, location obfuscation, and subject rights.
"""

from datetime import datetime
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from backend.models.entities import ConsentRecord, DataSubjectRequest, DataRetentionPolicy, Farmer, User
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import NotFoundError, ValidationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.security.privacy")


class PrivacyService:
    def __init__(self, db: Session):
        self.db = db
        self.blur_decimals = int(config_manager.get("privacy.location_privacy_decimals"))

    def record_consent(
        self,
        farmer_id: int,
        consent_purpose: str,
        consent_version: str = "v1.0",
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ConsentRecord:
        """Records granular, purpose-bound farmer consent."""
        farmer = self.db.scalars(select(Farmer).where(Farmer.id == farmer_id)).first()
        if not farmer:
            raise NotFoundError(message=f"Farmer {farmer_id} not found.", entity="Farmer")

        # Check existing active consent for this specific purpose
        existing = self.db.scalars(
            select(ConsentRecord).where(
                and_(
                    ConsentRecord.farmer_id == farmer_id,
                    ConsentRecord.consent_purpose == consent_purpose,
                    ConsentRecord.is_granted == True
                )
            )
        ).first()

        if existing:
            existing.consent_timestamp = datetime.utcnow()
            existing.consent_version = consent_version
            existing.ip_address = ip_address
            existing.notes = notes
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = ConsentRecord(
            farmer_id=farmer_id,
            user_id=user_id,
            consent_purpose=consent_purpose,
            consent_version=consent_version,
            is_granted=True,
            consent_timestamp=datetime.utcnow(),
            ip_address=ip_address,
            notes=notes
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info(f"Recorded consent purpose '{consent_purpose}' for farmer ID {farmer_id}.")
        return record

    def withdraw_consent(self, consent_id: int, user_id: Optional[int] = None) -> ConsentRecord:
        """Executes consent withdrawal for a specific processing purpose."""
        consent = self.db.scalars(select(ConsentRecord).where(ConsentRecord.id == consent_id)).first()
        if not consent:
            raise NotFoundError(message=f"Consent record {consent_id} not found.", entity="ConsentRecord")

        consent.is_granted = False
        consent.withdrawn_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(consent)
        logger.info(f"Withdrawn consent purpose '{consent.consent_purpose}' (Record {consent_id}).")
        return consent

    def list_consents_for_farmer(self, farmer_id: int) -> List[ConsentRecord]:
        """Lists active and historical consent records for a farmer."""
        return list(
            self.db.scalars(
                select(ConsentRecord)
                .where(ConsentRecord.farmer_id == farmer_id)
                .order_by(desc(ConsentRecord.consent_timestamp))
            ).all()
        )

    def submit_subject_request(
        self,
        user_id: int,
        request_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> DataSubjectRequest:
        """Submits a formal Data Subject Access/Correction/Erasure Request."""
        valid_types = ["ACCESS", "CORRECTION", "ERASURE", "EXPORT"]
        if request_type.upper() not in valid_types:
            raise ValidationError(
                message=f"Invalid request type '{request_type}'. Must be one of {valid_types}.",
                field="request_type"
            )

        dsr = DataSubjectRequest(
            user_id=user_id,
            request_type=request_type.upper(),
            status="SUBMITTED",
            details_json=details or {},
            requested_at=datetime.utcnow()
        )
        self.db.add(dsr)
        self.db.commit()
        self.db.refresh(dsr)
        logger.info(f"Submitted Data Subject Request ID {dsr.id} ({request_type}) for user {user_id}.")
        return dsr

    def list_subject_requests(self, user_id: Optional[int] = None) -> List[DataSubjectRequest]:
        """Queries DSR queue."""
        query = select(DataSubjectRequest)
        if user_id is not None:
            query = query.where(DataSubjectRequest.user_id == user_id)
        query = query.order_by(desc(DataSubjectRequest.requested_at))
        return list(self.db.scalars(query).all())

    def filter_location_privacy(
        self,
        latitude: float,
        longitude: float,
        viewer_role: Optional[str] = None,
        is_owner: bool = False,
        use_metric_scaling: bool = False
    ) -> Tuple[float, float, bool]:
        """
        Enforces geospatial privacy protection under DPDP Act 2023.
        Truncates coordinates to 2 decimal places (~1.1 km precision) for public/unprivileged viewers.
        Optionally applies latitude-scaled metric tensor scaling (scaled by 1/cos(lat)).
        Returns (lat, lon, is_blurred).
        """
        role = (viewer_role or "PUBLIC_VISITOR").upper()
        # Privileged roles or parcel owners receive unblurred coordinates
        if is_owner or role in ["SYSTEM_ADMINISTRATOR", "ORGANIZATION_MANAGER", "FIELD_OPERATOR"]:
            return (latitude, longitude, False)

        blurred_lat = round(latitude, self.blur_decimals)
        if use_metric_scaling:
            lat_rad = math.radians(latitude)
            cos_lat = max(math.cos(lat_rad), 0.1)  # Guard against poles
            step_lat = 10 ** (-self.blur_decimals)
            step_lon = step_lat / cos_lat
            blurred_lon = round(round(longitude / step_lon) * step_lon, self.blur_decimals)
        else:
            blurred_lon = round(longitude, self.blur_decimals)

        return (blurred_lat, blurred_lon, True)
