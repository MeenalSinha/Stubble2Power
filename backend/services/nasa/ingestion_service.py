"""
NASA Ingestion Pipeline Orchestrator.
Manages job lifecycle, API communication, immutable raw record preservation,
and handoff to the Quality Control service.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.nasa.client import NASAClient
from backend.services.fire.quality_service import QualityControlService
from backend.repositories.satellite_repository import SatelliteRepository
from backend.schemas.satellite import IngestionJobResponse
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.nasa.ingestion")


class IngestionService:
    def __init__(self, db: Session, client: Optional[NASAClient] = None):
        self.db = db
        self.client = client or NASAClient()
        self.repo = SatelliteRepository(db)

    def run_country_ingestion(
        self,
        country_code: str = "IND",
        source: str = "VIIRS_NOAA20_NRT",
        day_range: int = 1,
        date_str: Optional[str] = None,
    ) -> IngestionJobResponse:
        """
        Executes end-to-end ingestion job for a country.
        1. Creates IngestionJob record in state PENDING
        2. Queries NASA FIRMS
        3. Stores immutable raw observations
        4. Normalizes and validates via QualityControlService
        5. Persists canonical observations
        6. Updates IngestionJob state to COMPLETED or FAILED
        """
        job_uuid = str(uuid.uuid4())
        today = date.today()
        d_start = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else today

        source_meta = self.client.VALID_SOURCES.get(source, {"instrument": "UNKNOWN", "satellite": "UNKNOWN"})
        endpoint_repr = f"/api/country/{source}/{country_code}/{day_range}"

        job = self.repo.create_ingestion_job(
            job_uuid=job_uuid,
            satellite=source_meta["satellite"],
            instrument=source_meta["instrument"],
            source_endpoint=endpoint_repr,
            date_start=d_start,
            date_end=d_start,
        )

        try:
            self.repo.update_job_status(job.id, "RUNNING")
            raw_records = self.client.fetch_country_fires(
                country_code=country_code, source=source, day_range=day_range, date_str=date_str
            )

            # 1. Immutable raw storage
            for r in raw_records:
                rec_hash = QualityControlService.generate_observation_hash(
                    satellite=r.get("_satellite", "UNKNOWN"),
                    instrument=r.get("_instrument", "UNKNOWN"),
                    acq_date_str=str(r.get("acq_date")),
                    acq_time_str=str(r.get("acq_time", "0000")),
                    lat=float(r.get("latitude", 0.0)),
                    lon=float(r.get("longitude", 0.0)),
                )
                self.repo.insert_raw_observation(job.id, rec_hash, source, r)

            # 2. Quality control and normalization
            normalized_list, summary = QualityControlService.batch_process(raw_records)

            # 3. Canonical persistent storage
            valid_inserted = 0
            quarantined_inserted = 0
            for norm in normalized_list:
                if self.repo.insert_normalized_observation(norm, job.id):
                    if norm.is_valid:
                        valid_inserted += 1
                    else:
                        quarantined_inserted += 1

            self.db.commit()

            final_status = "COMPLETED" if summary.invalid_quarantined_records == 0 else "COMPLETED_WITH_WARNINGS"
            updated_job = self.repo.update_job_status(
                job_id=job.id,
                status=final_status,
                records_retrieved=len(raw_records),
                records_valid=valid_inserted,
                records_quarantined=quarantined_inserted,
            )
            return IngestionJobResponse.model_validate(updated_job)

        except Exception as e:
            self.db.rollback()
            error_msg = str(e)
            logger.error(f"Ingestion job {job_uuid} failed: {error_msg}")
            updated_job = self.repo.update_job_status(job_id=job.id, status="FAILED", error_message=error_msg)
            return IngestionJobResponse.model_validate(updated_job)

    def run_area_ingestion(
        self, bbox: List[float], source: str = "VIIRS_NOAA20_NRT", day_range: int = 1, date_str: Optional[str] = None
    ) -> IngestionJobResponse:
        """Executes bounding-box ingestion job."""
        job_uuid = str(uuid.uuid4())
        today = date.today()
        d_start = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else today

        source_meta = self.client.VALID_SOURCES.get(source, {"instrument": "UNKNOWN", "satellite": "UNKNOWN"})
        endpoint_repr = f"/api/area/{source}/{bbox}/{day_range}"

        job = self.repo.create_ingestion_job(
            job_uuid=job_uuid,
            satellite=source_meta["satellite"],
            instrument=source_meta["instrument"],
            source_endpoint=endpoint_repr,
            date_start=d_start,
            date_end=d_start,
        )

        try:
            self.repo.update_job_status(job.id, "RUNNING")
            raw_records = self.client.fetch_area_fires(bbox=bbox, source=source, day_range=day_range, date_str=date_str)

            for r in raw_records:
                rec_hash = QualityControlService.generate_observation_hash(
                    satellite=r.get("_satellite", "UNKNOWN"),
                    instrument=r.get("_instrument", "UNKNOWN"),
                    acq_date_str=str(r.get("acq_date")),
                    acq_time_str=str(r.get("acq_time", "0000")),
                    lat=float(r.get("latitude", 0.0)),
                    lon=float(r.get("longitude", 0.0)),
                )
                self.repo.insert_raw_observation(job.id, rec_hash, source, r)

            normalized_list, summary = QualityControlService.batch_process(raw_records)

            valid_inserted = 0
            quarantined_inserted = 0
            for norm in normalized_list:
                if self.repo.insert_normalized_observation(norm, job.id):
                    if norm.is_valid:
                        valid_inserted += 1
                    else:
                        quarantined_inserted += 1

            self.db.commit()

            final_status = "COMPLETED" if summary.invalid_quarantined_records == 0 else "COMPLETED_WITH_WARNINGS"
            updated_job = self.repo.update_job_status(
                job_id=job.id,
                status=final_status,
                records_retrieved=len(raw_records),
                records_valid=valid_inserted,
                records_quarantined=quarantined_inserted,
            )
            return IngestionJobResponse.model_validate(updated_job)

        except Exception as e:
            self.db.rollback()
            error_msg = str(e)
            logger.error(f"Ingestion job {job_uuid} failed: {error_msg}")
            updated_job = self.repo.update_job_status(job_id=job.id, status="FAILED", error_message=error_msg)
            return IngestionJobResponse.model_validate(updated_job)
