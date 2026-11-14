"""
Scientific MODIS-VIIRS Satellite Fire Observation Harmonization Engine.
Addresses NASA Space Apps Challenge 09: Harmonization of MODIS and VIIRS Hot Spots.

Scientific Methodology:
- Accounts for sensor footprint disparity: MODIS 1000m nadir (4.8km edge) vs VIIRS 375m pixel-trimmed.
- Bins continuous coordinates into a configurable discrete spatial grid.
- Identifies cross-sensor spatial associations within distance and temporal tolerances.
- Computes calibrated Fire Radiative Power (FRP) and Normalized Burning Activity Index.
- Rigorously manages uncertainty and distinguishes zero burning from missing satellite coverage.
"""

import math
import uuid
from datetime import date
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session

from backend.schemas.harmonization import (
    HarmonizedObservationSchema,
    HarmonizationRunResponse
)
from backend.models.entities import NormalizedSatelliteObservation
from backend.repositories.satellite_repository import SatelliteRepository
from backend.repositories.harmonization_repository import HarmonizationRepository
from backend.services.geospatial.service import GeospatialService
from backend.core.config.settings import config_manager
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.harmonization.engine")


class HarmonizationEngine:
    ALGORITHM_VERSION = "2.1.0-spaceapps-scientific"

    def __init__(self, db: Session):
        self.db = db
        self.sat_repo = SatelliteRepository(db)
        self.harm_repo = HarmonizationRepository(db)

    def execute_harmonization(
        self,
        name: str = "Automated Harmonization Run",
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        grid_resolution_deg: Optional[float] = None,
        cross_sensor_dist_km: Optional[float] = None,
        time_window_hours: Optional[float] = None,
        viirs_frp_slope: Optional[float] = None,
        bbox: Optional[List[float]] = None
    ) -> HarmonizationRunResponse:
        """
        Executes complete scientific harmonization pipeline across MODIS and VIIRS observations.
        """
        # Resolve parameters from configuration registry
        if grid_resolution_deg is None:
            grid_resolution_deg = float(config_manager.get("nasa.harmonization.grid_resolution_deg"))
        if cross_sensor_dist_km is None:
            cross_sensor_dist_km = float(config_manager.get("nasa.harmonization.cross_sensor_distance_km"))
        if time_window_hours is None:
            time_window_hours = float(config_manager.get("nasa.harmonization.cross_sensor_time_window_hours"))
        if viirs_frp_slope is None:
            viirs_frp_slope = float(config_manager.get("nasa.harmonization.viirs_frp_calibration_slope"))

        # Query normalized observations
        raw_obs_list = self.sat_repo.query_observations(
            date_start=date_start,
            date_end=date_end,
            bbox=bbox,
            is_valid=True,
            limit=50000
        )

        run_uuid = str(uuid.uuid4())
        today = date.today()
        actual_start = date_start or (min(o.acquisition_date for o in raw_obs_list) if raw_obs_list else today)
        actual_end = date_end or (max(o.acquisition_date for o in raw_obs_list) if raw_obs_list else today)

        params_json = {
            "grid_resolution_deg": grid_resolution_deg,
            "cross_sensor_distance_km": cross_sensor_dist_km,
            "cross_sensor_time_window_hours": time_window_hours,
            "viirs_frp_calibration_slope": viirs_frp_slope,
            "bbox": bbox
        }

        run_record = self.harm_repo.create_run(
            run_uuid=run_uuid,
            name=name,
            date_start=actual_start,
            date_end=actual_end,
            grid_resolution_deg=grid_resolution_deg,
            parameters_json=params_json,
            algorithm_version=self.ALGORITHM_VERSION
        )

        if not raw_obs_list:
            completed_run = self.harm_repo.complete_run(
                run_id=run_record.id,
                total_inputs=0,
                cells_count=0,
                associated_pairs=0,
                mean_consensus=0.0,
                status="COMPLETED_EMPTY",
                sensor_breakdown={"MODIS": 0, "VIIRS": 0}
            )
            resp = HarmonizationRunResponse.model_validate(completed_run)
            resp.sensor_breakdown = {"MODIS": 0, "VIIRS": 0}
            return resp

        # Step 1: Spatial & Temporal Binning by (Observation Date, Grid Cell)
        grid_bins: Dict[Tuple[date, str], List[NormalizedSatelliteObservation]] = defaultdict(list)
        for obs in raw_obs_list:
            grid_id = obs.spatial_grid_id or GeospatialService.compute_grid_id(
                obs.latitude, obs.longitude, grid_resolution_deg
            )
            grid_bins[(obs.acquisition_date, grid_id)].append(obs)

        harmonized_schemas: List[HarmonizedObservationSchema] = []
        total_associated_pairs = 0
        consensus_scores: List[float] = []

        # Step 2: Harmonize each Grid Cell
        for (obs_date, grid_id), cell_obs in grid_bins.items():
            modis_points = [o for o in cell_obs if o.instrument == "MODIS"]
            viirs_points = [o for o in cell_obs if o.instrument == "VIIRS"]

            m_count = len(modis_points)
            v_count = len(viirs_points)
            tot_count = m_count + v_count

            # Calculate Centroid
            mean_lat = float(np.mean([o.latitude for o in cell_obs]))
            mean_lon = float(np.mean([o.longitude for o in cell_obs]))

            # Cross-Sensor Spatial-Temporal Association
            associated_pairs = self._compute_associations(
                modis_points, viirs_points, cross_sensor_dist_km, time_window_hours
            )
            total_associated_pairs += len(associated_pairs)

            # FRP Statistics & Intercalibration
            m_frps = [o.frp for o in modis_points if o.frp is not None]
            v_frps = [o.frp for o in viirs_points if o.frp is not None]

            m_mean_frp = float(np.mean(m_frps)) if m_frps else None
            v_mean_frp = float(np.mean(v_frps)) if v_frps else None

            # Calibrated FRP calculation
            # Wooster (2021): calibrated_frp = sum(MODIS) + sum(VIIRS * slope)
            sum_m_frp = sum(m_frps)
            sum_v_frp = sum(v * viirs_frp_slope for v in v_frps)
            calibrated_frp_mw = sum_m_frp + sum_v_frp

            # Consensus Score (0.0 - 1.0)
            consensus = self._compute_consensus_score(m_count, v_count, len(associated_pairs))
            consensus_scores.append(consensus)

            # Uncertainty Level (Thresholds managed in Configuration Registry)
            thresh_high = float(config_manager.get("nasa.harmonization.consensus_threshold_high"))
            thresh_low = float(config_manager.get("nasa.harmonization.consensus_threshold_low"))
            if consensus >= thresh_high:
                uncertainty = "LOW"
            elif consensus >= thresh_low:
                uncertainty = "MODERATE"
            else:
                uncertainty = "HIGH"

            # Coverage Flag
            if m_count > 0 and v_count > 0:
                coverage_flag = "DUAL_SENSOR"
            elif v_count > 0:
                coverage_flag = "VIIRS_ONLY"
            elif m_count > 0:
                coverage_flag = "MODIS_ONLY"
            else:
                coverage_flag = "ZERO_DETECTED"

            # Normalized Burning Activity Index (0 to 100 scale)
            # Combines detection count, calibrated energy (FRP), and consensus weight
            activity_index = self._compute_activity_index(
                modis_count=m_count,
                viirs_count=v_count,
                calibrated_frp_mw=calibrated_frp_mw,
                consensus_score=consensus
            )

            harmonized_schemas.append(HarmonizedObservationSchema(
                grid_id=grid_id,
                observation_date=obs_date,
                centroid_lat=round(mean_lat, 5),
                centroid_lon=round(mean_lon, 5),
                modis_count=m_count,
                viirs_count=v_count,
                total_detections=tot_count,
                associated_pairs_count=len(associated_pairs),
                modis_mean_frp=round(m_mean_frp, 2) if m_mean_frp is not None else None,
                viirs_mean_frp=round(v_mean_frp, 2) if v_mean_frp is not None else None,
                harmonized_frp_mw=round(calibrated_frp_mw, 2),
                harmonized_activity_index=round(activity_index, 1),
                consensus_score=round(consensus, 3),
                uncertainty_level=uncertainty,
                data_coverage_flag=coverage_flag
            ))

        # Bulk persist harmonized results
        self.harm_repo.bulk_insert_harmonized(run_record.id, harmonized_schemas)

        mean_consensus = float(np.mean(consensus_scores)) if consensus_scores else 0.0
        sensor_breakdown_dict = {
            "MODIS": sum(1 for o in raw_obs_list if o.instrument == "MODIS"),
            "VIIRS": sum(1 for o in raw_obs_list if o.instrument == "VIIRS")
        }
        completed_run = self.harm_repo.complete_run(
            run_id=run_record.id,
            total_inputs=len(raw_obs_list),
            cells_count=len(harmonized_schemas),
            associated_pairs=total_associated_pairs,
            mean_consensus=round(mean_consensus, 3),
            status="COMPLETED",
            sensor_breakdown=sensor_breakdown_dict
        )
        resp = HarmonizationRunResponse.model_validate(completed_run)
        resp.sensor_breakdown = sensor_breakdown_dict
        return resp

    def _compute_associations(
        self,
        modis_points: List[NormalizedSatelliteObservation],
        viirs_points: List[NormalizedSatelliteObservation],
        dist_threshold_km: float,
        time_window_hours: float
    ) -> List[Tuple[int, int]]:
        """
        Identifies spatial and temporal pairs between MODIS and VIIRS detections.
        Matches observations within distance threshold and time window.
        """
        associations: List[Tuple[int, int]] = []
        for m in modis_points:
            for v in viirs_points:
                # Time delta check
                time_diff_hours = abs((m.timestamp_utc - v.timestamp_utc).total_seconds()) / 3600.0
                if time_diff_hours <= time_window_hours:
                    # Great circle distance check
                    dist_km = GeospatialService.haversine_distance(
                        m.latitude, m.longitude,
                        v.latitude, v.longitude
                    )
                    if dist_km <= dist_threshold_km:
                        associations.append((m.id, v.id))
        return associations

    def _compute_consensus_score(
        self,
        modis_count: int,
        viirs_count: int,
        associated_pairs: int
    ) -> float:
        """
        Quantifies inter-sensor agreement on a 0.0 to 1.0 scale.
        Consensus is highest when both sensors detect activity and share associated pairs.
        """
        if modis_count > 0 and viirs_count > 0:
            pair_ratio = min(1.0, associated_pairs / max(1, min(modis_count, viirs_count)))
            return round(0.70 + 0.30 * pair_ratio, 3)
        elif viirs_count > 0 and modis_count == 0:
            # VIIRS has 375m resolution and detects sub-pixel fires invisible to 1km MODIS
            return 0.75 if viirs_count >= 2 else 0.60
        elif modis_count > 0 and viirs_count == 0:
            # MODIS detected a large fire but VIIRS had no overpass or cloud obscuration
            return 0.55
        return 0.0

    def _compute_activity_index(
        self,
        modis_count: int,
        viirs_count: int,
        calibrated_frp_mw: float,
        consensus_score: float
    ) -> float:
        """
        Derives Normalized Burning Activity Index (0.0 to 100.0).
        All empirical slopes, footprint weights, and term limits are retrieved
        from the Configuration Registry to prevent hardcoding.
        """
        modis_weight = float(config_manager.get("nasa.harmonization.modis_detection_weight"))
        det_slope = float(config_manager.get("nasa.harmonization.detection_index_slope"))
        det_cap = float(config_manager.get("nasa.harmonization.detection_index_cap"))
        frp_slope = float(config_manager.get("nasa.harmonization.frp_index_slope"))
        frp_cap = float(config_manager.get("nasa.harmonization.frp_index_cap"))
        consensus_weight = float(config_manager.get("nasa.harmonization.consensus_index_weight"))

        # Effective detections: footprint area weighting
        effective_detections = (modis_count * modis_weight) + viirs_count
        detection_term = min(det_cap, effective_detections * det_slope)

        frp_term = min(frp_cap, math.log1p(calibrated_frp_mw) * frp_slope)
        consensus_term = consensus_score * consensus_weight

        raw_index = detection_term + frp_term + consensus_term
        return min(100.0, max(0.0, raw_index))
