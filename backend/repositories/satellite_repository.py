"""
Repository for NASA satellite raw and normalized observations, products, and ingestion jobs.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from backend.models.entities import (
    IngestionJob,
    RawSatelliteObservation,
    NormalizedSatelliteObservation
)
from backend.schemas.satellite import NormalizedObservationSchema


class SatelliteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_ingestion_job(
        self,
        job_uuid: str,
        satellite: str,
        instrument: str,
        source_endpoint: str,
        date_start: date,
        date_end: date
    ) -> IngestionJob:
        job = IngestionJob(
            job_uuid=job_uuid,
            satellite=satellite,
            instrument=instrument,
            source_endpoint=source_endpoint,
            date_start=date_start,
            date_end=date_end,
            status="PENDING"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_status(
        self,
        job_id: int,
        status: str,
        records_retrieved: int = 0,
        records_valid: int = 0,
        records_quarantined: int = 0,
        error_message: Optional[str] = None
    ) -> IngestionJob:
        job = self.db.get(IngestionJob, job_id)
        if job:
            job.status = status
            job.records_retrieved = records_retrieved
            job.records_valid = records_valid
            job.records_quarantined = records_quarantined
            job.error_message = error_message
            if status in ["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"]:
                job.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job

    def insert_raw_observation(self, ingestion_job_id: int, record_hash: str, satellite: str, raw_payload: dict) -> bool:
        # Idempotent insert
        exists = self.db.scalar(
            select(RawSatelliteObservation.id).where(RawSatelliteObservation.record_hash == record_hash)
        )
        if exists:
            return False

        raw_obs = RawSatelliteObservation(
            ingestion_job_id=ingestion_job_id,
            record_hash=record_hash,
            source_satellite=satellite,
            raw_payload=raw_payload
        )
        self.db.add(raw_obs)
        return True

    def insert_normalized_observation(self, obs: NormalizedObservationSchema, job_id: int) -> bool:
        exists = self.db.scalar(
            select(NormalizedSatelliteObservation.id).where(
                NormalizedSatelliteObservation.source_record_hash == obs.source_record_hash
            )
        )
        if exists:
            return False

        norm_obs = NormalizedSatelliteObservation(
            source_record_hash=obs.source_record_hash,
            ingestion_job_id=job_id,
            satellite=obs.satellite,
            instrument=obs.instrument,
            product_version=obs.product_version,
            acquisition_date=obs.acquisition_date,
            acquisition_time_utc=obs.acquisition_time_utc,
            timestamp_utc=obs.timestamp_utc,
            latitude=obs.latitude,
            longitude=obs.longitude,
            brightness=obs.brightness,
            bright_t31=obs.bright_t31,
            frp=obs.frp,
            confidence_raw=obs.confidence_raw,
            confidence_normalized=obs.confidence_normalized,
            daynight=obs.daynight,
            scan=obs.scan,
            track=obs.track,
            spatial_grid_id=obs.spatial_grid_id,
            is_valid=obs.is_valid,
            quarantine_reason=obs.quarantine_reason
        )
        self.db.add(norm_obs)
        return True

    def query_observations(
        self,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        instrument: Optional[str] = None,
        min_confidence: Optional[float] = None,
        bbox: Optional[List[float]] = None,
        is_valid: bool = True,
        limit: int = 5000
    ) -> List[NormalizedSatelliteObservation]:
        stmt = select(NormalizedSatelliteObservation).where(NormalizedSatelliteObservation.is_valid == is_valid)
        filters = []
        if date_start:
            filters.append(NormalizedSatelliteObservation.acquisition_date >= date_start)
        if date_end:
            filters.append(NormalizedSatelliteObservation.acquisition_date <= date_end)
        if instrument:
            filters.append(NormalizedSatelliteObservation.instrument.ilike(f"%{instrument}%"))
        if min_confidence is not None:
            filters.append(NormalizedSatelliteObservation.confidence_normalized >= min_confidence)
        if bbox and len(bbox) == 4:
            min_lon, min_lat, max_lon, max_lat = bbox
            filters.append(NormalizedSatelliteObservation.latitude.between(min_lat, max_lat))
            filters.append(NormalizedSatelliteObservation.longitude.between(min_lon, max_lon))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(NormalizedSatelliteObservation.timestamp_utc.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_ingestion_summary(self) -> Dict[str, Any]:
        total_norm = self.db.scalar(select(func.count(NormalizedSatelliteObservation.id))) or 0
        total_valid = self.db.scalar(
            select(func.count(NormalizedSatelliteObservation.id)).where(NormalizedSatelliteObservation.is_valid == True)
        ) or 0
        modis_count = self.db.scalar(
            select(func.count(NormalizedSatelliteObservation.id)).where(NormalizedSatelliteObservation.instrument == "MODIS")
        ) or 0
        viirs_count = self.db.scalar(
            select(func.count(NormalizedSatelliteObservation.id)).where(NormalizedSatelliteObservation.instrument == "VIIRS")
        ) or 0
        latest_date = self.db.scalar(select(func.max(NormalizedSatelliteObservation.acquisition_date)))
        earliest_date = self.db.scalar(select(func.min(NormalizedSatelliteObservation.acquisition_date)))

        return {
            "total_observations": total_norm,
            "valid_observations": total_valid,
            "modis_count": modis_count,
            "viirs_count": viirs_count,
            "earliest_date": str(earliest_date) if earliest_date else None,
            "latest_date": str(latest_date) if latest_date else None
        }
