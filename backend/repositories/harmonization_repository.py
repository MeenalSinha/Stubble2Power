"""
Repository for Harmonization Runs and Harmonized Observation grids.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from backend.models.entities import HarmonizationRun, HarmonizedObservation
from backend.schemas.harmonization import HarmonizedObservationSchema


class HarmonizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_run(
        self,
        run_uuid: str,
        name: str,
        date_start: date,
        date_end: date,
        grid_resolution_deg: float,
        parameters_json: dict,
        algorithm_version: str = "1.0.0-scientific",
    ) -> HarmonizationRun:
        run = HarmonizationRun(
            run_uuid=run_uuid,
            name=name,
            date_start=date_start,
            date_end=date_end,
            grid_resolution_deg=grid_resolution_deg,
            algorithm_version=algorithm_version,
            parameters_json=parameters_json,
            status="PENDING",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def complete_run(
        self,
        run_id: int,
        total_inputs: int,
        cells_count: int,
        associated_pairs: int,
        mean_consensus: float,
        status: str = "COMPLETED",
        sensor_breakdown: Optional[dict] = None,
    ) -> HarmonizationRun:
        run = self.db.get(HarmonizationRun, run_id)
        if run:
            run.total_input_observations = total_inputs
            run.harmonized_cells_count = cells_count
            run.associated_pairs_count = associated_pairs
            run.mean_consensus_score = mean_consensus
            run.status = status
            if sensor_breakdown is not None:
                run.sensor_breakdown = sensor_breakdown
            self.db.commit()
            self.db.refresh(run)
        return run

    def bulk_insert_harmonized(self, run_id: int, items: List[HarmonizedObservationSchema]) -> int:
        count = 0
        for item in items:
            obs = HarmonizedObservation(
                harmonization_run_id=run_id,
                grid_id=item.grid_id,
                observation_date=item.observation_date,
                centroid_lat=item.centroid_lat,
                centroid_lon=item.centroid_lon,
                modis_count=item.modis_count,
                viirs_count=item.viirs_count,
                total_detections=item.total_detections,
                associated_pairs_count=item.associated_pairs_count,
                modis_mean_frp=item.modis_mean_frp,
                viirs_mean_frp=item.viirs_mean_frp,
                harmonized_frp_mw=item.harmonized_frp_mw,
                harmonized_activity_index=item.harmonized_activity_index,
                consensus_score=item.consensus_score,
                uncertainty_level=item.uncertainty_level,
                data_coverage_flag=item.data_coverage_flag,
            )
            self.db.add(obs)
            count += 1
        self.db.commit()
        return count

    def get_latest_run(self) -> Optional[HarmonizationRun]:
        stmt = select(HarmonizationRun).order_by(HarmonizationRun.id.desc()).limit(1)
        return self.db.scalar(stmt)

    def query_harmonized(
        self,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        min_activity: Optional[float] = None,
        bbox: Optional[List[float]] = None,
        limit: int = 5000,
    ) -> List[HarmonizedObservation]:
        stmt = select(HarmonizedObservation)
        filters = []
        if date_start:
            filters.append(HarmonizedObservation.observation_date >= date_start)
        if date_end:
            filters.append(HarmonizedObservation.observation_date <= date_end)
        if min_activity is not None:
            filters.append(HarmonizedObservation.harmonized_activity_index >= min_activity)
        if bbox and len(bbox) == 4:
            min_lon, min_lat, max_lon, max_lat = bbox
            filters.append(HarmonizedObservation.centroid_lat.between(min_lat, max_lat))
            filters.append(HarmonizedObservation.centroid_lon.between(min_lon, max_lon))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(HarmonizedObservation.observation_date.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())
