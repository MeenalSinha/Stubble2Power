"""
Farm, Land, and Cultivation Management Service.
Handles multi-farm management per farmer, spatial boundary validation,
crop cycles, and harvest records with data privacy safeguards.
"""

from typing import List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.models.entities import Farmer, Farm, FarmCrop, HarvestRecord
from backend.services.geospatial.service import GeospatialService
from backend.core.exceptions.base import NotFoundError, ValidationError
from backend.core.logging.logger import get_logger
from backend.schemas.farm import FarmCreate, FarmCropCreate, HarvestRecordCreate

logger = get_logger("stubble2power.farms")


class FarmService:
    def __init__(self, db: Session):
        self.db = db
        self.geo_svc = GeospatialService()

    def create_farm(self, payload: FarmCreate) -> Farm:
        """Registers a new agricultural farm linked to a verified farmer."""
        # Validate parent farmer exists
        farmer = self.db.scalars(select(Farmer).where(Farmer.id == payload.farmer_id)).first()
        if not farmer:
            raise NotFoundError(message=f"Farmer with id {payload.farmer_id} not found.", entity="Farmer")

        # Validate coordinates
        self.geo_svc.validate_coordinates(payload.latitude, payload.longitude)

        farm = Farm(
            farmer_id=payload.farmer_id,
            farm_name=payload.farm_name,
            total_acres=round(payload.total_acres, 2),
            village=payload.village,
            district=payload.district,
            state=payload.state,
            latitude=payload.latitude,
            longitude=payload.longitude,
            ownership_status=payload.ownership_status,
            soil_type=payload.soil_type,
            boundary_geojson=payload.boundary_geojson,
            verification_status="VERIFIED",
        )
        self.db.add(farm)
        self.db.commit()
        self.db.refresh(farm)
        logger.info(f"Registered farm '{farm.farm_name}' ({farm.total_acres} acres) for farmer ID {farm.farmer_id}.")
        return farm

    def get_farm(self, farm_id: int) -> Farm:
        farm = self.db.scalars(select(Farm).where(Farm.id == farm_id)).first()
        if not farm:
            raise NotFoundError(message=f"Farm with id {farm_id} not found.", entity="Farm")
        return farm

    def list_farms(
        self,
        farmer_id: Optional[int] = None,
        district: Optional[str] = None,
        state: Optional[str] = None,
        soil_type: Optional[str] = None,
    ) -> List[Farm]:
        stmt = select(Farm)
        filters = []
        if farmer_id and isinstance(farmer_id, int):
            filters.append(Farm.farmer_id == farmer_id)
        if district and isinstance(district, str):
            filters.append(Farm.district.ilike(f"%{district}%"))
        if state and isinstance(state, str):
            filters.append(Farm.state.ilike(f"%{state}%"))
        if soil_type and isinstance(soil_type, str):
            filters.append(Farm.soil_type.ilike(f"%{soil_type}%"))
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(Farm.id)
        return list(self.db.scalars(stmt).all())

    def add_crop(self, payload: FarmCropCreate) -> FarmCrop:
        """Adds a seasonal crop cultivation record to a farm."""
        farm = self.get_farm(payload.farm_id)
        if payload.cultivated_acres > farm.total_acres:
            raise ValidationError(
                message=f"Cultivated acres ({payload.cultivated_acres}) cannot exceed farm total acres ({farm.total_acres}).",
                field="cultivated_acres",
            )

        crop = FarmCrop(
            farm_id=payload.farm_id,
            crop_type=payload.crop_type.upper(),
            cultivated_acres=round(payload.cultivated_acres, 2),
            crop_season=payload.crop_season,
            crop_year=payload.crop_year,
            sowing_date=payload.sowing_date,
            expected_harvest_date=payload.expected_harvest_date,
            expected_yield_tons_per_acre=payload.expected_yield_tons_per_acre,
            cultivation_status="ACTIVE",
        )
        self.db.add(crop)
        self.db.commit()
        self.db.refresh(crop)
        logger.info(f"Added crop {crop.crop_type} ({crop.cultivated_acres} ac) to farm {crop.farm_id}.")
        return crop

    def add_crop_cultivation(self, farm_id: int, payload: FarmCropCreate) -> FarmCrop:
        payload.farm_id = farm_id
        return self.add_crop(payload)

    def list_crops_for_farm(self, farm_id: int) -> List[FarmCrop]:
        stmt = select(FarmCrop).where(FarmCrop.farm_id == farm_id).order_by(FarmCrop.crop_year.desc())
        return list(self.db.scalars(stmt).all())

    def list_crops_by_farm(self, farm_id: int) -> List[FarmCrop]:
        return self.list_crops_for_farm(farm_id)

    def record_harvest(self, payload_or_crop_id: Any, payload: Optional[HarvestRecordCreate] = None) -> HarvestRecord:
        """Records actual grain harvest measurements for a farm crop."""
        if isinstance(payload_or_crop_id, int):
            actual_payload = payload
            if actual_payload:
                actual_payload.farm_crop_id = payload_or_crop_id
        else:
            actual_payload = payload_or_crop_id

        if not actual_payload:
            raise ValidationError(message="Harvest record payload is required.", field="harvest_record")

        crop = self.db.scalars(select(FarmCrop).where(FarmCrop.id == actual_payload.farm_crop_id)).first()
        if not crop:
            raise NotFoundError(
                message=f"Farm crop with id {actual_payload.farm_crop_id} not found.", entity="FarmCrop"
            )

        harvest = HarvestRecord(
            farm_crop_id=actual_payload.farm_crop_id,
            harvest_date=actual_payload.harvest_date,
            actual_grain_yield_tons=round(actual_payload.actual_grain_yield_tons, 2),
            grain_moisture_pct=actual_payload.grain_moisture_pct,
            harvest_method=actual_payload.harvest_method,
            is_measured=actual_payload.is_measured,
            notes=actual_payload.notes,
        )
        # Update crop record with actual metrics
        crop.actual_harvest_date = actual_payload.harvest_date
        crop.actual_yield_tons_per_acre = round(
            actual_payload.actual_grain_yield_tons / max(0.1, crop.cultivated_acres), 2
        )
        crop.cultivation_status = "HARVESTED"

        self.db.add(harvest)
        self.db.commit()
        self.db.refresh(harvest)
        logger.info(f"Recorded harvest of {harvest.actual_grain_yield_tons}t for crop ID {crop.id}.")
        return harvest
