"""
Mobile Bio-Refinery Fleet & Capability Management Service.
Manages trailer-mounted mobile densification units, pyrolysis rigs, operating costs, and availability.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.models.entities import MobileBioRefinery
from backend.core.exceptions.base import NotFoundError, ValidationError
from backend.core.logging.logger import get_logger
from backend.schemas.deployment import MobileRefineryCreate

logger = get_logger("stubble2power.deployment.refinery")


class MobileRefineryService:
    def __init__(self, db: Session):
        self.db = db

    def register_unit(self, payload: MobileRefineryCreate) -> MobileBioRefinery:
        """Registers a new mobile bio-refinery unit into the operational fleet."""
        existing = self.db.scalars(select(MobileBioRefinery).where(MobileBioRefinery.unit_code == payload.unit_code)).first()
        if existing:
            raise ValidationError(message=f"Unit code '{payload.unit_code}' is already registered.", field="unit_code")

        daily_cap = payload.hourly_capacity_tons * payload.daily_operating_hours
        unit = MobileBioRefinery(
            unit_code=payload.unit_code.upper(),
            name=payload.name,
            equipment_type=payload.equipment_type,
            technology=payload.technology,
            hourly_capacity_tons=payload.hourly_capacity_tons,
            daily_operating_hours=payload.daily_operating_hours,
            daily_capacity_tons=round(daily_cap, 2),
            fuel_consumption_liters_per_ton=payload.fuel_consumption_liters_per_ton,
            operating_cost_per_hour_inr=payload.operating_cost_per_hour_inr,
            current_status="AVAILABLE",
            home_depot_name=payload.home_depot_name,
            home_latitude=payload.home_latitude,
            home_longitude=payload.home_longitude,
            max_travel_radius_km=payload.max_travel_radius_km,
            is_active=True
        )
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        logger.info(f"Registered mobile unit {unit.unit_code} ({unit.daily_capacity_tons}t/day capacity).")
        return unit

    def get_unit(self, unit_id: int) -> MobileBioRefinery:
        unit = self.db.scalars(select(MobileBioRefinery).where(MobileBioRefinery.id == unit_id)).first()
        if not unit:
            raise NotFoundError(message=f"Mobile unit {unit_id} not found.", entity="MobileBioRefinery")
        return unit

    def list_units(
        self,
        status: Optional[str] = None,
        technology: Optional[str] = None
    ) -> List[MobileBioRefinery]:
        stmt = select(MobileBioRefinery).where(MobileBioRefinery.is_active == True)
        filters = []
        if status and isinstance(status, str):
            filters.append(MobileBioRefinery.current_status == status.upper())
        if technology and isinstance(technology, str):
            filters.append(MobileBioRefinery.technology == technology.upper())
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(MobileBioRefinery.unit_code)
        return list(self.db.scalars(stmt).all())

    def update_status(self, unit_id: int, new_status: str) -> MobileBioRefinery:
        unit = self.get_unit(unit_id)
        unit.current_status = new_status.upper()
        self.db.commit()
        self.db.refresh(unit)
        logger.info(f"Updated unit {unit.unit_code} status to '{unit.current_status}'.")
        return unit
