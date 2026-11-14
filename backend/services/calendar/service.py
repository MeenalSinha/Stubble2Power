"""
Historical Burning Activity Calendar Service.
Dynamically aggregates harmonized daily, weekly, monthly, and seasonal satellite fire activity.
Distinguishes real zero burning from lack of satellite overpass coverage.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import calendar
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from backend.models.entities import HarmonizedObservation, NormalizedSatelliteObservation
from backend.schemas.calendar import (
    DailyCalendarEntry,
    WeeklyCalendarSummary,
    MonthlyCalendarSummary,
    AnnualCalendarSummary
)


class CalendarAggregationService:
    def __init__(self, db: Session):
        self.db = db

    def get_daily_calendar(
        self,
        date_start: date,
        date_end: date,
        bbox: Optional[List[float]] = None
    ) -> List[DailyCalendarEntry]:
        """
        Derives continuous daily calendar entries from harmonized database records.
        Fills missing days with ZERO_BURNING or NO_OVERPASS flags.
        """
        # Query harmonized observations in range
        stmt = select(HarmonizedObservation).where(
            and_(
                HarmonizedObservation.observation_date >= date_start,
                HarmonizedObservation.observation_date <= date_end
            )
        )
        if bbox and len(bbox) == 4:
            min_lon, min_lat, max_lon, max_lat = bbox
            stmt = stmt.where(
                and_(
                    HarmonizedObservation.centroid_lat.between(min_lat, max_lat),
                    HarmonizedObservation.centroid_lon.between(min_lon, max_lon)
                )
            )

        harmonized_records = list(self.db.scalars(stmt).all())

        # Group by date
        date_groups: Dict[date, List[HarmonizedObservation]] = {}
        for r in harmonized_records:
            date_groups.setdefault(r.observation_date, []).append(r)

        calendar_entries: List[DailyCalendarEntry] = []
        curr_date = date_start
        delta = timedelta(days=1)

        while curr_date <= date_end:
            records = date_groups.get(curr_date, [])
            if records:
                m_count = sum(r.modis_count for r in records)
                v_count = sum(r.viirs_count for r in records)
                tot_count = sum(r.total_detections for r in records)
                assoc_count = sum(r.associated_pairs_count for r in records)
                tot_frp = sum(r.harmonized_frp_mw for r in records)
                mean_activity = float(sum(r.harmonized_activity_index for r in records) / len(records))

                if m_count > 0 and v_count > 0:
                    status = "COMPLETE"
                elif v_count > 0:
                    status = "PARTIAL_VIIRS"
                elif m_count > 0:
                    status = "PARTIAL_MODIS"
                else:
                    status = "ZERO_BURNING"

                calendar_entries.append(DailyCalendarEntry(
                    date=curr_date,
                    day_of_week=curr_date.strftime("%A"),
                    modis_detections=m_count,
                    viirs_detections=v_count,
                    total_detections=tot_count,
                    associated_detections=assoc_count,
                    harmonized_activity_index=round(mean_activity, 1),
                    total_frp_mw=round(tot_frp, 1),
                    coverage_status=status
                ))
            else:
                # Distinguish whether normalized data exists on this date
                obs_count = self.db.scalar(
                    select(func.count(NormalizedSatelliteObservation.id)).where(
                        NormalizedSatelliteObservation.acquisition_date == curr_date
                    )
                ) or 0

                status = "ZERO_BURNING" if obs_count > 0 else "NO_OVERPASS"
                calendar_entries.append(DailyCalendarEntry(
                    date=curr_date,
                    day_of_week=curr_date.strftime("%A"),
                    modis_detections=0,
                    viirs_detections=0,
                    total_detections=0,
                    associated_detections=0,
                    harmonized_activity_index=0.0,
                    total_frp_mw=0.0,
                    coverage_status=status
                ))

            curr_date += delta

        return calendar_entries

    def get_monthly_summaries(
        self,
        year: int,
        bbox: Optional[List[float]] = None
    ) -> List[MonthlyCalendarSummary]:
        """Aggregates monthly burning metrics for an entire annual cycle."""
        summaries: List[MonthlyCalendarSummary] = []

        for month in range(1, 13):
            last_day = calendar.monthrange(year, month)[1]
            d_start = date(year, month, 1)
            d_end = date(year, month, last_day)

            daily = self.get_daily_calendar(d_start, d_end, bbox)
            tot_detections = sum(d.total_detections for d in daily)
            m_detections = sum(d.modis_detections for d in daily)
            v_detections = sum(d.viirs_detections for d in daily)
            active_days = sum(1 for d in daily if d.total_detections > 0)
            mean_act = float(sum(d.harmonized_activity_index for d in daily) / len(daily)) if daily else 0.0

            peak_d = None
            peak_count = 0
            for d in daily:
                if d.total_detections > peak_count:
                    peak_count = d.total_detections
                    peak_d = d.date

            summaries.append(MonthlyCalendarSummary(
                year=year,
                month=month,
                month_name=calendar.month_name[month],
                total_detections=tot_detections,
                modis_detections=m_detections,
                viirs_detections=v_detections,
                mean_daily_activity=round(mean_act, 1),
                active_burning_days=active_days,
                peak_date=peak_d,
                peak_detections=peak_count
            ))

        return summaries

    def get_annual_summary(
        self,
        year: int,
        bbox: Optional[List[float]] = None
    ) -> AnnualCalendarSummary:
        """Derives annual trend and detects seasonal burning boundaries (Oct-Nov peak in Punjab)."""
        monthly = self.get_monthly_summaries(year, bbox)
        total_det = sum(m.total_detections for m in monthly)
        modis_det = sum(m.modis_detections for m in monthly)
        viirs_det = sum(m.viirs_detections for m in monthly)

        # Identify peak month
        peak_month = max(monthly, key=lambda m: m.total_detections) if total_det > 0 else None
        season_peak = peak_month.peak_date if peak_month else None

        # Post-monsoon Kharif burning season typically spans October 1 to November 30
        season_start = date(year, 10, 1)
        season_end = date(year, 11, 30)
        seasonal_daily = self.get_daily_calendar(season_start, season_end, bbox)
        seasonal_tot = sum(d.total_detections for d in seasonal_daily)

        return AnnualCalendarSummary(
            year=year,
            total_detections=total_det,
            modis_detections=modis_det,
            viirs_detections=viirs_det,
            burning_season_start=season_start,
            burning_season_peak=season_peak,
            burning_season_end=season_end,
            seasonal_total_detections=seasonal_tot
        )
