"""
Crop Calendar Reference Service.
Manages authoritative agricultural schedules (sowing, harvest, peak residue burn windows)
from official sources (ICAR, PAU, Ministry of Agriculture & Farmers Welfare).
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.models.entities import CropCalendar
from backend.core.config.settings import config_manager
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.agriculture.calendar")

# Official default reference crop calendars
DEFAULT_CROP_CALENDARS = [
    {
        "crop_name": "Paddy / Rice (Kharif)",
        "state_name": "Punjab",
        "district_name": "ALL",
        "season_name": "Kharif",
        "sowing_start_month_day": "06-15",
        "sowing_end_month_day": "07-15",
        "harvest_start_month_day": "10-01",
        "harvest_end_month_day": "11-30",
        "peak_burn_start_month_day": "10-15",
        "peak_burn_end_month_day": "11-20",
        "stubble_burning_susceptibility": "HIGH",
        "official_source": "Punjab Agricultural University (PAU) Crop Production Package",
        "citation": "PAU Ludhiana Agronomy Guidelines & ICAR-CSSRI Karnal Stubble Advisory (2024)",
        "version": "1.0.0"
    },
    {
        "crop_name": "Wheat (Rabi)",
        "state_name": "Punjab",
        "district_name": "ALL",
        "season_name": "Rabi",
        "sowing_start_month_day": "11-01",
        "sowing_end_month_day": "12-15",
        "harvest_start_month_day": "04-10",
        "harvest_end_month_day": "05-25",
        "peak_burn_start_month_day": "04-20",
        "peak_burn_end_month_day": "05-15",
        "stubble_burning_susceptibility": "MEDIUM",
        "official_source": "Indian Council of Agricultural Research (ICAR)",
        "citation": "ICAR Kharif/Rabi National Crop Production Directory",
        "version": "1.0.0"
    },
    {
        "crop_name": "Cotton (Kharif)",
        "state_name": "Punjab",
        "district_name": "ALL",
        "season_name": "Kharif",
        "sowing_start_month_day": "04-15",
        "sowing_end_month_day": "05-20",
        "harvest_start_month_day": "10-15",
        "harvest_end_month_day": "12-15",
        "peak_burn_start_month_day": "11-01",
        "peak_burn_end_month_day": "12-05",
        "stubble_burning_susceptibility": "LOW",
        "official_source": "Central Institute for Cotton Research (CICR)",
        "citation": "CICR Annual Agro-Advisory Series",
        "version": "1.0.0"
    },
    {
        "crop_name": "Sugarcane (Perennial)",
        "state_name": "Punjab",
        "district_name": "ALL",
        "season_name": "Perennial",
        "sowing_start_month_day": "02-15",
        "sowing_end_month_day": "04-01",
        "harvest_start_month_day": "11-15",
        "harvest_end_month_day": "03-31",
        "peak_burn_start_month_day": "12-01",
        "peak_burn_end_month_day": "02-15",
        "stubble_burning_susceptibility": "MEDIUM",
        "official_source": "Sugarcane Breeding Institute (ICAR-SBI)",
        "citation": "ICAR-SBI Production & Trash Management Advisory",
        "version": "1.0.0"
    }
]


class CropCalendarService:
    def __init__(self, db: Session):
        self.db = db
        self.extended_days = int(config_manager.get("agriculture.crop_calendar.extended_window_days"))
        self._ensure_reference_data_seeded()

    def _ensure_reference_data_seeded(self) -> None:
        """Seeds default official crop calendars if database table is empty."""
        count = self.db.query(CropCalendar).count()
        if count == 0:
            for item in DEFAULT_CROP_CALENDARS:
                cal = CropCalendar(**item)
                self.db.add(cal)
            self.db.commit()
            logger.info(f"Seeded {len(DEFAULT_CROP_CALENDARS)} official crop calendars.")

    def get_all_calendars(self, state_name: Optional[str] = None) -> List[CropCalendar]:
        """Lists active crop calendars."""
        stmt = select(CropCalendar).where(CropCalendar.is_active == True)
        if state_name:
            stmt = stmt.where(CropCalendar.state_name == state_name)
        return list(self.db.scalars(stmt).all())

    def match_harvest_window(
        self,
        obs_date: date,
        state_name: str = "Punjab",
        crop_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determines if an observation date falls in peak harvest, extended harvest, or off-season.
        Returns matched crop name, status, and susceptibility.
        """
        calendars = self.get_all_calendars(state_name=state_name)
        if crop_name:
            calendars = [c for c in calendars if crop_name.lower() in c.crop_name.lower()]

        year = obs_date.year
        matched_extended: Optional[Dict[str, Any]] = None

        for cal in calendars:
            # Parse month-day into actual dates for the observation year
            try:
                p_start_m, p_start_d = map(int, cal.peak_burn_start_month_day.split("-"))
                p_end_m, p_end_d = map(int, cal.peak_burn_end_month_day.split("-"))
                h_start_m, h_start_d = map(int, cal.harvest_start_month_day.split("-"))
                h_end_m, h_end_d = map(int, cal.harvest_end_month_day.split("-"))

                # Support cross-year windows (e.g. Dec to Feb, Nov to March)
                if p_end_m < p_start_m:
                    if obs_date.month <= p_end_m:
                        peak_start = date(year - 1, p_start_m, p_start_d)
                        peak_end = date(year, p_end_m, p_end_d)
                    else:
                        peak_start = date(year, p_start_m, p_start_d)
                        peak_end = date(year + 1, p_end_m, p_end_d)
                else:
                    peak_start = date(year, p_start_m, p_start_d)
                    peak_end = date(year, p_end_m, p_end_d)

                if h_end_m < h_start_m:
                    if obs_date.month <= h_end_m:
                        harvest_start = date(year - 1, h_start_m, h_start_d)
                        harvest_end = date(year, h_end_m, h_end_d)
                    else:
                        harvest_start = date(year, h_start_m, h_start_d)
                        harvest_end = date(year + 1, h_end_m, h_end_d)
                else:
                    harvest_start = date(year, h_start_m, h_start_d)
                    harvest_end = date(year, h_end_m, h_end_d)

                ext_start = harvest_start - timedelta(days=self.extended_days)
                ext_end = harvest_end + timedelta(days=self.extended_days)

                # Prioritize peak window match across any calendar
                if peak_start <= obs_date <= peak_end:
                    return {
                        "status": "IN_PEAK_HARVEST_WINDOW",
                        "matched_crop": cal.crop_name,
                        "season": cal.season_name,
                        "susceptibility": cal.stubble_burning_susceptibility,
                        "source": cal.official_source
                    }

                # Remember extended window match if no peak match is found later
                if matched_extended is None and (ext_start <= obs_date <= ext_end):
                    matched_extended = {
                        "status": "IN_EXTENDED_HARVEST_WINDOW",
                        "matched_crop": cal.crop_name,
                        "season": cal.season_name,
                        "susceptibility": cal.stubble_burning_susceptibility,
                        "source": cal.official_source
                    }
            except Exception as e:
                logger.warning(f"Error parsing date window for {cal.crop_name}: {str(e)}")
                continue

        if matched_extended:
            return matched_extended

        return {
            "status": "OFF_SEASON",
            "matched_crop": None,
            "season": "None",
            "susceptibility": "LOW",
            "source": "None"
        }
