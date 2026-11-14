"""
Agricultural Biomass Generation & Estimation Service.
Configurable mathematical residue estimation accounting for crop-specific Residue-to-Product Ratios,
in-situ soil retention, competing fodder demand, mechanical handling losses, and moisture adjustments.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.models.entities import FarmCrop, HarvestRecord, BiomassEstimate, BiomassInventoryTransaction
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import NotFoundError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.biomass.estimation")


class BiomassEstimationService:
    def __init__(self, db: Session):
        self.db = db
        # Configurable scientific parameters
        self.rpr_paddy = float(config_manager.get("biomass.paddy.residue_to_product_ratio"))
        self.rpr_wheat = float(config_manager.get("biomass.wheat.residue_to_product_ratio"))
        self.rpr_cotton = float(config_manager.get("biomass.cotton.residue_to_product_ratio"))
        self.paddy_collectable_frac = float(config_manager.get("biomass.paddy.sustainable_collection_fraction"))
        self.wheat_collectable_frac = float(config_manager.get("biomass.wheat.sustainable_collection_fraction"))
        self.handling_loss_frac = float(config_manager.get("biomass.collection_handling_loss_fraction"))
        self.default_moisture = float(config_manager.get("biomass.standard_moisture_content_pct"))
        self.default_paddy_yield = float(config_manager.get("biomass.paddy.default_grain_yield_tons_per_acre"))

    def estimate_crop_biomass(
        self,
        farm_crop_id: int,
        actual_grain_yield_tons: Optional[float] = None,
        moisture_pct: Optional[float] = None,
        retained_override: Optional[float] = None,
        competing_override: Optional[float] = None,
        persist: bool = True
    ) -> BiomassEstimate:
        """
        Executes evidence-based crop residue calculation following estimation hierarchy:
        1. Measured grain harvest -> 2. Farmer reported -> 3. Farm crop yield -> 4. Regional baseline.
        """
        crop = self.db.scalars(select(FarmCrop).where(FarmCrop.id == farm_crop_id)).first()
        if not crop:
            raise NotFoundError(message=f"Farm crop with id {farm_crop_id} not found.", entity="FarmCrop")

        # 1. Check for attached measured harvest record
        harvest = self.db.scalars(
            select(HarvestRecord).where(HarvestRecord.farm_crop_id == farm_crop_id).order_by(HarvestRecord.id.desc())
        ).first()

        # Determine grain production source
        if actual_grain_yield_tons is not None:
            grain_production = actual_grain_yield_tons
            source = "MEASURED"
            conf = 0.98
        elif harvest:
            grain_production = harvest.actual_grain_yield_tons
            source = "MEASURED" if harvest.is_measured else "FARMER_REPORTED"
            conf = 0.95 if harvest.is_measured else 0.88
        elif crop.actual_yield_tons_per_acre:
            grain_production = crop.actual_yield_tons_per_acre * crop.cultivated_acres
            source = "FARMER_REPORTED"
            conf = 0.85
        else:
            # Fallback to crop expected yield or regional statistics
            grain_production = (crop.expected_yield_tons_per_acre or self.default_paddy_yield) * crop.cultivated_acres
            source = "OFFICIAL_STATISTICS"
            conf = 0.78

        # 2. Select crop-specific RPR and sustainable retention/competing factors
        crop_type = crop.crop_type.upper()
        if "PADDY" in crop_type or "RICE" in crop_type:
            rpr = self.rpr_paddy
            # 25% retained for soil organic carbon, 0% cattle fodder (silica content high)
            retained_frac = 0.25 if retained_override is None else retained_override
            competing_frac = 0.00 if competing_override is None else competing_override
        elif "WHEAT" in crop_type:
            rpr = self.rpr_wheat
            # Wheat straw is prized for dairy cattle feed (bhusa), typically 60% priority domestic use
            retained_frac = 0.10 if retained_override is None else retained_override
            competing_frac = 0.50 if competing_override is None else competing_override
        elif "COTTON" in crop_type:
            rpr = self.rpr_cotton
            retained_frac = 0.15 if retained_override is None else retained_override
            competing_frac = 0.10 if competing_override is None else competing_override
        else:
            rpr = 1.40
            retained_frac = 0.20 if retained_override is None else retained_override
            competing_frac = 0.10 if competing_override is None else competing_override

        # 3. Mathematical Residue Quantities
        gross_residue = grain_production * rpr
        retained_residue = gross_residue * retained_frac
        competing_demand = gross_residue * competing_frac
        collectable_residue = max(0.0, gross_residue - retained_residue - competing_demand)

        handling_loss = collectable_residue * self.handling_loss_frac
        net_usable = max(0.0, collectable_residue - handling_loss)

        moisture = moisture_pct if moisture_pct is not None else (harvest.grain_moisture_pct if harvest else self.default_moisture)
        dry_matter = net_usable * (1.0 - (moisture / 100.0))

        # Availability window
        base_date = harvest.harvest_date if harvest else (crop.actual_harvest_date or crop.expected_harvest_date or date.today())
        start_date = base_date + timedelta(days=1)
        end_date = start_date + timedelta(days=25)  # 25-day field collection turnaround window

        notes = (
            f"Calculated using {crop_type} RPR of {rpr:.2f} based on {grain_production:.1f}t grain. "
            f"Retained {retained_frac*100:.0f}% for soil conservation, {competing_frac*100:.0f}% for competing fodder. "
            f"Net usable after {self.handling_loss_frac*100:.0f}% mechanical collection losses."
        )

        estimate = BiomassEstimate(
            farm_crop_id=farm_crop_id,
            harvest_record_id=harvest.id if harvest else None,
            gross_residue_tons=round(gross_residue, 2),
            retained_residue_tons=round(retained_residue, 2),
            competing_demand_tons=round(competing_demand, 2),
            collectable_residue_tons=round(collectable_residue, 2),
            handling_loss_tons=round(handling_loss, 2),
            net_usable_biomass_tons=round(net_usable, 2),
            moisture_content_pct=round(moisture, 1),
            dry_matter_tons=round(dry_matter, 2),
            estimation_source=source,
            confidence_score=round(conf, 2),
            availability_start_date=start_date,
            availability_end_date=end_date,
            methodology_notes=notes
        )

        if persist:
            self.db.add(estimate)
            self.db.flush()
            # Record initial inventory transaction
            tx = BiomassInventoryTransaction(
                biomass_estimate_id=estimate.id,
                farm_id=crop.farm_id,
                quantity_tons=round(net_usable, 2),
                stage="ESTIMATED",
                notes=f"Initial biomass estimation generated from {source}."
            )
            self.db.add(tx)
            self.db.commit()
            self.db.refresh(estimate)
            logger.info(f"Generated biomass estimate {estimate.net_usable_biomass_tons}t for crop ID {farm_crop_id}.")

        return estimate

    def get_estimate(self, estimate_id: int) -> BiomassEstimate:
        est = self.db.scalars(select(BiomassEstimate).where(BiomassEstimate.id == estimate_id)).first()
        if not est:
            raise NotFoundError(message=f"Biomass estimate {estimate_id} not found.", entity="BiomassEstimate")
        return est

    def list_estimates_for_crop(self, farm_crop_id: int) -> List[BiomassEstimate]:
        return list(
            self.db.scalars(
                select(BiomassEstimate)
                .where(BiomassEstimate.farm_crop_id == farm_crop_id)
                .order_by(BiomassEstimate.created_at.desc())
            ).all()
        )
