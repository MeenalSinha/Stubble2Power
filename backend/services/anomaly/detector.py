"""
Multi-Method Statistical Fire Activity Anomaly Detector.
Integrates parametric Z-Score, robust Median Absolute Deviation (MAD),
Exponentially Weighted Moving Average (EWMA), and spatial cluster analysis.
"""

from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.models.entities import FireActivityAnomaly, HarmonizedObservation, HistoricalBaseline
from backend.services.seasonal.baseline_service import HistoricalBaselineService
from backend.services.anomaly.explanation_service import AnomalyExplanationService
from backend.services.geospatial.service import GeospatialService
from backend.core.config.settings import config_manager
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.anomaly.detector")


class StatisticalAnomalyDetector:
    def __init__(self, db: Session):
        self.db = db
        self.baseline_svc = HistoricalBaselineService(db)
        self.geo_svc = GeospatialService()
        from backend.services.agriculture.crop_calendar_service import CropCalendarService

        self.crop_cal_svc = CropCalendarService(db)
        self.zscore_thresh = float(config_manager.get("anomaly.detection.zscore_threshold"))
        self.mad_thresh = float(config_manager.get("anomaly.detection.mad_threshold"))
        self.ewma_alpha = float(config_manager.get("anomaly.detection.ewma_alpha"))
        self.min_frp = float(config_manager.get("anomaly.detection.min_frp_mw"))
        self.cluster_radius_km = float(config_manager.get("anomaly.spatial.cluster_radius_km"))
        self.fallback_mean = float(config_manager.get("seasonal.baseline.fallback_mean"))
        self.fallback_median = float(config_manager.get("seasonal.baseline.fallback_median"))
        self.fallback_std = float(config_manager.get("seasonal.baseline.fallback_std"))
        self.fallback_mad = float(config_manager.get("seasonal.baseline.fallback_mad"))

    def detect_anomalies(
        self,
        date_start: date,
        date_end: date,
        region_id: str = "Punjab",
        zscore_threshold: Optional[float] = None,
        mad_threshold: Optional[float] = None,
        min_frp_mw: Optional[float] = None,
        persist: bool = True,
    ) -> List[FireActivityAnomaly]:
        """
        Executes multi-method statistical anomaly detection across all harmonized fire cells
        within the specified date interval.
        """
        z_th = zscore_threshold if zscore_threshold is not None else self.zscore_thresh
        mad_th = mad_threshold if mad_threshold is not None else self.mad_thresh
        frp_floor = min_frp_mw if min_frp_mw is not None else self.min_frp

        # 1. Fetch harmonized observations in range
        stmt = select(HarmonizedObservation).where(
            and_(
                HarmonizedObservation.observation_date >= date_start, HarmonizedObservation.observation_date <= date_end
            )
        )
        obs_records = list(self.db.scalars(stmt).all())
        if not obs_records:
            logger.info(f"No harmonized observations found between {date_start} and {date_end}.")
            return []

        # 2. Pre-fetch historical baselines
        all_baselines = self.baseline_svc.get_all_baselines(region_id=region_id, metric_type="harmonized_frp_mw")
        baseline_by_doy: Dict[int, HistoricalBaseline] = {
            b.day_of_year: b for b in all_baselines if b.day_of_year is not None
        }
        fallback_baseline = all_baselines[0] if all_baselines else None

        detected_anomalies: List[FireActivityAnomaly] = []

        # Spatial cluster co-occurrence lookup per date
        date_coords_map: Dict[date, List[tuple]] = {}
        for r in obs_records:
            date_coords_map.setdefault(r.observation_date, []).append((r.centroid_lat, r.centroid_lon))

        for obs in obs_records:
            activity_val = float(obs.harmonized_frp_mw or obs.harmonized_activity_index or 0.0)
            if activity_val < frp_floor:
                continue

            doy = obs.observation_date.timetuple().tm_yday
            baseline = baseline_by_doy.get(doy) or fallback_baseline

            if baseline:
                exp_mean = baseline.mean_val
                exp_median = baseline.median_val
                std_val = max(1.0, baseline.std_val)
                mad_val = max(0.5, baseline.mad_val)
                data_sufficiency = baseline.data_sufficiency_status
            else:
                # Evidence-based baseline priors loaded from ConfigManager
                exp_mean = self.fallback_mean
                exp_median = self.fallback_median
                std_val = max(1.0, self.fallback_std)
                mad_val = max(0.5, self.fallback_mad)
                data_sufficiency = "LIMITED_HISTORY"

            # Compute parametric Z-score and robust MAD score
            z_score = (activity_val - exp_mean) / std_val
            mad_score = (activity_val - exp_median) / mad_val

            # Compute EWMA tracking score
            ewma_baseline = (self.ewma_alpha * activity_val) + ((1.0 - self.ewma_alpha) * exp_mean)
            ewma_score = (activity_val - ewma_baseline) / std_val

            # Spatial cluster check
            same_day_coords = date_coords_map.get(obs.observation_date, [])
            co_occurring_count = 0
            for lat, lon in same_day_coords:
                if (lat, lon) != (obs.centroid_lat, obs.centroid_lon):
                    dist = self.geo_svc.haversine_distance_km(obs.centroid_lat, obs.centroid_lon, lat, lon)
                    if dist <= self.cluster_radius_km:
                        co_occurring_count += 1

            # Anomaly criteria evaluation
            is_anomaly = False
            anomaly_type = "SPIKE"

            # Check unseasonal burning via authoritative crop calendar harvest windows
            harvest_match = self.crop_cal_svc.match_harvest_window(obs.observation_date, state_name=region_id)
            is_unseasonal = harvest_match["status"] == "OFF_SEASON"

            if mad_score >= mad_th or z_score >= z_th:
                is_anomaly = True
                if is_unseasonal:
                    anomaly_type = "UNSEASONAL_TIMING"
                elif co_occurring_count >= 5:
                    anomaly_type = "SPATIAL_CLUSTER"
                else:
                    anomaly_type = "SPIKE"
            elif is_unseasonal and activity_val >= (frp_floor * 2.0):
                is_anomaly = True
                anomaly_type = "UNSEASONAL_TIMING"
            elif co_occurring_count >= 8:
                is_anomaly = True
                anomaly_type = "SPATIAL_CLUSTER"

            if not is_anomaly:
                continue

            # Severity determination
            if mad_score >= 4.5 or (z_score >= 4.0 and activity_val >= 50.0):
                severity = "CRITICAL"
            elif mad_score >= mad_th or z_score >= z_th:
                severity = "HIGH"
            elif mad_score >= 2.0 or z_score >= 2.0:
                severity = "MODERATE"
            else:
                severity = "LOW"

            # Data sufficiency flag
            sufficiency_flag = "SUFFICIENT" if data_sufficiency == "SUFFICIENT" else "UNCERTAIN_LIMITED_BASELINE"

            explanation = AnomalyExplanationService.generate_explanation(
                observation_date=obs.observation_date,
                grid_id=obs.grid_id,
                region_id=region_id,
                observed_val=activity_val,
                baseline_val=exp_median,
                metric_name="Harmonized FRP (MW)",
                z_score=z_score,
                mad_score=mad_score,
                anomaly_type=anomaly_type,
                severity_level=severity,
                data_sufficiency_status=data_sufficiency,
                co_occurring_count=co_occurring_count,
            )

            anomaly_record = FireActivityAnomaly(
                observation_date=obs.observation_date,
                grid_id=obs.grid_id,
                region_id=region_id,
                observed_activity=round(activity_val, 2),
                baseline_metric="harmonized_frp_mw",
                baseline_value=round(exp_median, 2),
                z_score=round(z_score, 2),
                mad_score=round(mad_score, 2),
                ewma_score=round(ewma_score, 2),
                anomaly_type=anomaly_type,
                severity_level=severity,
                data_sufficiency_flag=sufficiency_flag,
                explanation_json=explanation,
                centroid_lat=obs.centroid_lat,
                centroid_lon=obs.centroid_lon,
            )
            detected_anomalies.append(anomaly_record)

        if persist and detected_anomalies:
            # Clear previous anomalies in range for region
            self.db.query(FireActivityAnomaly).filter(
                and_(
                    FireActivityAnomaly.region_id == region_id,
                    FireActivityAnomaly.observation_date >= date_start,
                    FireActivityAnomaly.observation_date <= date_end,
                )
            ).delete()
            self.db.add_all(detected_anomalies)
            self.db.commit()
            logger.info(f"Persisted {len(detected_anomalies)} anomalies for {region_id}.")

        return detected_anomalies

    def get_anomalies(
        self,
        region_id: Optional[str] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        severity_level: Optional[str] = None,
    ) -> List[FireActivityAnomaly]:
        """Lists detected fire activity anomalies with flexible filters."""
        stmt = select(FireActivityAnomaly)
        filters = []
        if region_id:
            filters.append(FireActivityAnomaly.region_id == region_id)
        if date_start:
            filters.append(FireActivityAnomaly.observation_date >= date_start)
        if date_end:
            filters.append(FireActivityAnomaly.observation_date <= date_end)
        if severity_level:
            filters.append(FireActivityAnomaly.severity_level == severity_level)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(FireActivityAnomaly.observation_date.desc(), FireActivityAnomaly.observed_activity.desc())
        return list(self.db.scalars(stmt).all())
