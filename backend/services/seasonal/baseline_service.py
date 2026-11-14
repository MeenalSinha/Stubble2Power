"""
Historical Baseline Calculation Service.
Computes multi-year statistical normals, rolling medians, MAD, standard deviations,
and data sufficiency checks for regional satellite fire activity.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from backend.models.entities import HistoricalBaseline, HarmonizedObservation, DailyActivityAggregate
from backend.core.config.settings import config_manager
from backend.core.logging.logger import get_logger
from backend.schemas.seasonal import BaselineComputeRequest, BaselineEntry

logger = get_logger("stubble2power.seasonal.baseline")


class HistoricalBaselineService:
    def __init__(self, db: Session):
        self.db = db
        self.min_periods = int(config_manager.get("seasonal.baseline.min_historical_periods"))
        self.rolling_window = int(config_manager.get("seasonal.baseline.rolling_window_days"))
        self.min_coverage_pct = float(config_manager.get("seasonal.baseline.min_coverage_pct"))

    def compute_baselines_from_data(
        self,
        daily_records: List[Dict[str, Any]],
        region_id: str = "Punjab",
        analysis_period: str = "OCT_NOV_MULTIYEAR",
        metric_type: str = "harmonized_frp_mw",
        persist: bool = True
    ) -> List[HistoricalBaseline]:
        """
        Computes robust baseline statistics (Mean, Median, Std, MAD, P75, P90)
        from a collection of daily records across multiple years or dates.
        """
        if not daily_records:
            logger.warning(f"No daily records provided for baseline calculation in {region_id}.")
            return []

        df = pd.DataFrame(daily_records)
        if "date" not in df.columns or metric_type not in df.columns:
            logger.error(f"Missing required columns in daily data: 'date' and '{metric_type}'.")
            return []

        df["date"] = pd.to_datetime(df["date"])
        # Standardize leap years to standard 365-day calendar so identical dates across years map to the same DOY
        is_leap = df["date"].dt.is_leap_year
        raw_doy = df["date"].dt.dayofyear
        df["day_of_year"] = np.where(is_leap & (raw_doy > 60), raw_doy - 1, raw_doy)
        
        # Do not convert missing measurements to 0.0 (missing != zero burning)
        df["metric"] = pd.to_numeric(df[metric_type], errors="coerce")
        # Keep coverage flag if supplied
        has_coverage_col = "coverage_ratio" in df.columns or "data_coverage_ratio" in df.columns
        cov_col = "coverage_ratio" if "coverage_ratio" in df.columns else "data_coverage_ratio"

        results: List[HistoricalBaseline] = []

        # Group by day of year for seasonal cycle baseline
        grouped = df.groupby("day_of_year")
        for doy, group in grouped:
            # Exclude missing observations from values
            valid_vals = group["metric"].dropna().values
            n_samples = len(valid_vals)
            
            if n_samples == 0:
                continue

            # Genuine coverage measurement
            if has_coverage_col:
                coverage_ratio = float(group[cov_col].mean())
            else:
                total_expected_slots = len(group)
                coverage_ratio = n_samples / max(1, total_expected_slots)

            mean_val = float(np.mean(valid_vals))
            median_val = float(np.median(valid_vals))
            std_val = float(np.std(valid_vals, ddof=1)) if n_samples > 1 else 0.0
            
            # Robust Median Absolute Deviation (MAD) scaled by 1.4826 for normal consistency
            abs_devs = np.abs(valid_vals - median_val)
            mad_val = float(1.4826 * np.median(abs_devs))
            if mad_val < 1e-4:
                # If median absolute deviation is near zero, fallback to standard deviation or minimum floor
                mad_val = max(std_val * 0.6745, 0.5)

            p75_val = float(np.percentile(valid_vals, 75))
            p90_val = float(np.percentile(valid_vals, 90))
            min_val = float(np.min(valid_vals))
            max_val = float(np.max(valid_vals))

            # Data sufficiency evaluation
            if n_samples < self.min_periods:
                sufficiency = "LIMITED_HISTORY"
            elif (coverage_ratio * 100.0) < self.min_coverage_pct:
                sufficiency = "INSUFFICIENT_COVERAGE"
            else:
                sufficiency = "SUFFICIENT"

            baseline_record = HistoricalBaseline(
                region_id=region_id,
                grid_id=None,
                analysis_period=analysis_period,
                metric_type=metric_type,
                day_of_year=int(doy),
                mean_val=round(mean_val, 3),
                median_val=round(median_val, 3),
                std_val=round(std_val, 3),
                mad_val=round(mad_val, 3),
                p75_val=round(p75_val, 3),
                p90_val=round(p90_val, 3),
                min_val=round(min_val, 3),
                max_val=round(max_val, 3),
                sample_count=n_samples,
                data_coverage_ratio=round(coverage_ratio, 3),
                data_sufficiency_status=sufficiency
            )
            results.append(baseline_record)

        if persist and results:
            # Clear previous entries for same region, period and metric
            self.db.query(HistoricalBaseline).filter(
                and_(
                    HistoricalBaseline.region_id == region_id,
                    HistoricalBaseline.analysis_period == analysis_period,
                    HistoricalBaseline.metric_type == metric_type
                )
            ).delete()
            self.db.add_all(results)
            self.db.commit()
            logger.info(f"Persisted {len(results)} baseline records for {region_id} ({metric_type}).")

        return results

    def get_baseline_for_day(
        self,
        region_id: str,
        metric_type: str,
        day_of_year: int,
        search_window_days: int = 7
    ) -> Optional[HistoricalBaseline]:
        """
        Retrieves baseline profile for a day of year in the given region.
        Searches exact day first; if absent, searches nearest adjacent day within search_window_days.
        Never silently returns an arbitrary unrelated day.
        """
        stmt = select(HistoricalBaseline).where(
            and_(
                HistoricalBaseline.region_id == region_id,
                HistoricalBaseline.metric_type == metric_type,
                HistoricalBaseline.day_of_year == day_of_year
            )
        )
        baseline = self.db.scalars(stmt).first()
        if baseline:
            return baseline

        # Nearest day search strictly within search_window_days
        min_doy = max(1, day_of_year - search_window_days)
        max_doy = min(365, day_of_year + search_window_days)
        stmt_window = select(HistoricalBaseline).where(
            and_(
                HistoricalBaseline.region_id == region_id,
                HistoricalBaseline.metric_type == metric_type,
                HistoricalBaseline.day_of_year.between(min_doy, max_doy)
            )
        ).order_by(func.abs(HistoricalBaseline.day_of_year - day_of_year))
        
        adjacent = self.db.scalars(stmt_window).first()
        return adjacent

    def get_all_baselines(
        self,
        region_id: Optional[str] = None,
        metric_type: Optional[str] = None
    ) -> List[HistoricalBaseline]:
        """Lists baselines with optional region and metric filtering."""
        stmt = select(HistoricalBaseline)
        filters = []
        if region_id:
            filters.append(HistoricalBaseline.region_id == region_id)
        if metric_type:
            filters.append(HistoricalBaseline.metric_type == metric_type)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(HistoricalBaseline.day_of_year)
        return list(self.db.scalars(stmt).all())
