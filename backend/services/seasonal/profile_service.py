"""
Seasonal Profile Generation Service.
Generates empirical burning activity profiles, determines onset, peak, and decay dates,
and computes seasonal cumulative distributions from harmonized satellite observations.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.models.entities import SeasonalProfile, HarmonizedObservation, DailyActivityAggregate
from backend.core.logging.logger import get_logger
from backend.schemas.seasonal import SeasonalProfileCreate, SeasonalProfileResponse

logger = get_logger("stubble2power.seasonal.profile")


class SeasonalProfileService:
    def __init__(self, db: Session):
        self.db = db

    def generate_profile(
        self,
        region_id: str,
        year: int,
        season_name: str,
        date_start: date,
        date_end: date,
        persist: bool = True
    ) -> SeasonalProfile:
        """
        Derives an empirical seasonal profile from harmonized observations in the date window.
        Calculates onset, peak, and decay dates, total volume, and temporal curve.
        """
        # Query harmonized daily observations
        stmt = select(HarmonizedObservation).where(
            and_(
                HarmonizedObservation.observation_date >= date_start,
                HarmonizedObservation.observation_date <= date_end
            )
        )
        records = list(self.db.scalars(stmt).all())

        # Aggregate daily total activity index and FRP
        daily_map: Dict[date, float] = {}
        curr = date_start
        while curr <= date_end:
            daily_map[curr] = 0.0
            curr += timedelta(days=1)

        for r in records:
            daily_map[r.observation_date] = daily_map.get(r.observation_date, 0.0) + (r.harmonized_frp_mw or r.harmonized_activity_index or 0.0)

        dates_sorted = sorted(daily_map.keys())
        activity_vals = [daily_map[d] for d in dates_sorted]
        cum_vals = np.cumsum(activity_vals).tolist()
        total_activity = float(cum_vals[-1]) if cum_vals else 0.0

        onset_date: Optional[date] = None
        peak_date: Optional[date] = None
        decay_date: Optional[date] = None
        peak_activity = 0.0

        if total_activity > 0 and len(activity_vals) > 0:
            peak_idx = int(np.argmax(activity_vals))
            peak_date = dates_sorted[peak_idx]
            peak_activity = float(activity_vals[peak_idx])

            # Onset: First day where cumulative activity >= 10% of total
            onset_threshold = 0.10 * total_activity
            for d, cum in zip(dates_sorted, cum_vals):
                if cum >= onset_threshold:
                    onset_date = d
                    break

            # Decay: Day after peak where cumulative activity reaches 90% of total
            decay_threshold = 0.90 * total_activity
            for d, cum in zip(dates_sorted, cum_vals):
                if cum >= decay_threshold:
                    decay_date = d
                    break

        duration_days = 0
        if onset_date and decay_date:
            duration_days = max(1, (decay_date - onset_date).days + 1)
        elif date_start and date_end:
            duration_days = (date_end - date_start).days + 1

        curve_payload = {
            "dates": [d.isoformat() for d in dates_sorted],
            "daily_activity": [round(float(v), 2) for v in activity_vals],
            "cumulative_activity": [round(float(v), 2) for v in cum_vals],
            "total_records_processed": len(records)
        }

        # Check existing profile
        existing_stmt = select(SeasonalProfile).where(
            and_(
                SeasonalProfile.region_id == region_id,
                SeasonalProfile.year == year,
                SeasonalProfile.season_name == season_name
            )
        )
        profile = self.db.scalars(existing_stmt).first()

        if profile:
            profile.onset_date = onset_date
            profile.peak_date = peak_date
            profile.decay_date = decay_date
            profile.total_activity = round(total_activity, 2)
            profile.peak_activity = round(peak_activity, 2)
            profile.duration_days = duration_days
            profile.profile_curve_json = curve_payload
        else:
            profile = SeasonalProfile(
                region_id=region_id,
                year=year,
                season_name=season_name,
                onset_date=onset_date,
                peak_date=peak_date,
                decay_date=decay_date,
                total_activity=round(total_activity, 2),
                peak_activity=round(peak_activity, 2),
                duration_days=duration_days,
                profile_curve_json=curve_payload
            )
            self.db.add(profile)

        if persist:
            self.db.commit()
            self.db.refresh(profile)
            logger.info(f"Generated seasonal profile {season_name} {year} for {region_id}.")

        return profile

    def get_profiles(self, region_id: Optional[str] = None) -> List[SeasonalProfile]:
        """Lists historical seasonal profiles."""
        stmt = select(SeasonalProfile)
        if region_id:
            stmt = stmt.where(SeasonalProfile.region_id == region_id)
        stmt = stmt.order_by(SeasonalProfile.year.desc())
        return list(self.db.scalars(stmt).all())
