"""
Agricultural Biomass Generation & Estimation Service.
Configurable mathematical residue estimation accounting for crop-specific Residue-to-Product Ratios,
in-situ soil retention, competing fodder demand, mechanical handling losses, and moisture adjustments.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.entities import FarmCrop, HarvestRecord, BiomassEstimate, BiomassInventoryTransaction
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import NotFoundError, ValidationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.biomass.estimation")


class BiomassEstimationService:
    def __init__(self, db: Session):
        self.db = db
        # Configurable scientific parameters from ConfigManager
        self.rpr_table: Dict[str, float] = config_manager.get("biomass.crop_rpr_table")
        self.baseline_yields: Dict[str, float] = config_manager.get("biomass.crop_baseline_yields_tons_per_acre")
        self.retained_fractions: Dict[str, float] = config_manager.get("biomass.crop_retained_fractions")
        self.competing_fractions: Dict[str, float] = config_manager.get("biomass.crop_competing_fractions")
        self.confidence_scores: Dict[str, float] = config_manager.get("biomass.confidence_by_source")
        self.collection_window_days: int = int(config_manager.get("biomass.collection_window_days"))
        self.handling_loss_frac = float(config_manager.get("biomass.collection_handling_loss_fraction"))
        self.default_moisture = float(config_manager.get("biomass.standard_moisture_content_pct"))

    def _normalize_crop_key(self, crop_type: str) -> str:
        ct = crop_type.upper()
        if "PADDY" in ct or "RICE" in ct:
            return "PADDY_RICE"
        if "WHEAT" in ct:
            return "WHEAT"
        if "COTTON" in ct:
            return "COTTON"
        if "MAIZE" in ct or "CORN" in ct:
            return "MAIZE"
        if "SUGARCANE" in ct:
            return "SUGARCANE"
        return ct

    def estimate_crop_biomass(
        self,
        farm_crop_id: int,
        actual_grain_yield_tons: Optional[float] = None,
        moisture_pct: Optional[float] = None,
        retained_override: Optional[float] = None,
        competing_override: Optional[float] = None,
        persist: bool = True,
    ) -> BiomassEstimate:
        """
        Executes evidence-based crop residue calculation following estimation hierarchy:
        1. Measured grain harvest -> 2. Farmer reported -> 3. Farm crop yield -> 4. Regional baseline.
        """
        crop = self.db.scalars(select(FarmCrop).where(FarmCrop.id == farm_crop_id)).first()
        if not crop:
            raise NotFoundError(message=f"Farm crop with id {farm_crop_id} not found.", entity="FarmCrop")

        crop_key = self._normalize_crop_key(crop.crop_type)

        # 1. Check for attached measured harvest record
        harvest = self.db.scalars(
            select(HarvestRecord).where(HarvestRecord.farm_crop_id == farm_crop_id).order_by(HarvestRecord.id.desc())
        ).first()

        # Determine grain production source
        if actual_grain_yield_tons is not None:
            grain_production = actual_grain_yield_tons
            source = "MEASURED"
            conf = self.confidence_scores.get("MEASURED_ACTUAL", 0.98)
        elif harvest:
            grain_production = harvest.actual_grain_yield_tons
            source = "MEASURED" if harvest.is_measured else "FARMER_REPORTED"
            conf = (
                self.confidence_scores.get("MEASURED_HARVEST", 0.95)
                if harvest.is_measured
                else self.confidence_scores.get("FARMER_REPORTED_HARVEST", 0.88)
            )
        elif crop.actual_yield_tons_per_acre:
            grain_production = crop.actual_yield_tons_per_acre * crop.cultivated_acres
            source = "FARMER_REPORTED"
            conf = self.confidence_scores.get("FARMER_REPORTED_CROP", 0.85)
        else:
            # Fallback to crop expected yield or regional statistics for that specific crop
            crop_baseline = crop.expected_yield_tons_per_acre or self.baseline_yields.get(crop_key)
            if crop_baseline is None:
                raise ValidationError(
                    message=f"Cannot estimate biomass: No yield or regional baseline found for crop '{crop.crop_type}'.",
                    field="crop_type",
                )
            grain_production = crop_baseline * crop.cultivated_acres
            source = "OFFICIAL_STATISTICS"
            conf = self.confidence_scores.get("REGIONAL_BASELINE", 0.78)

        # 2. Select crop-specific RPR and sustainable retention/competing factors
        if crop_key in self.rpr_table:
            rpr = self.rpr_table[crop_key]
        else:
            raise ValidationError(
                message=f"Unrecognized crop type '{crop.crop_type}'. No validated Residue-to-Product Ratio found.",
                field="crop_type",
            )

        default_retained = self.retained_fractions.get(crop_key, 0.20)
        default_competing = self.competing_fractions.get(crop_key, 0.10)

        retained_frac = default_retained if retained_override is None else retained_override
        competing_frac = default_competing if competing_override is None else competing_override

        # 3. Mathematical Stage-Gate Residue Mass-Balance
        # Stage 1: Gross Agronomic Residue (Product-to-Residue agronomic baseline)
        gross_residue = grain_production * rpr

        # Stage 2: In-Situ Soil Conservation & Competing Fodder (Allocated from Gross Residue)
        retained_residue = gross_residue * retained_frac
        competing_demand = gross_residue * competing_frac

        # Stage 3: Field-Collectable Biomass Pool
        # Denominator basis: Residue physically left on field available for collection equipment
        collectable_residue = max(0.0, gross_residue - retained_residue - competing_demand)

        # Stage 4: Collection, Baling, and Handling Losses
        # CRITICAL METHODOLOGICAL SPECIFICATION (DENOMINATOR):
        # Handling loss fraction (f_loss = 0.08) operates strictly on the FIELD-COLLECTABLE residue pool
        # (collectable_residue), NOT gross residue. Stubble already retained in soil or diverted to livestock
        # does not enter the mechanical baling/transit chain and cannot incur logistics handling loss.
        # Formula: handling_loss = collectable_residue * handling_loss_frac
        # Net Usable: net_usable = collectable_residue * (1.0 - handling_loss_frac)
        handling_loss = collectable_residue * self.handling_loss_frac
        net_usable = max(0.0, collectable_residue - handling_loss)

        moisture = (
            moisture_pct
            if moisture_pct is not None
            else (harvest.grain_moisture_pct if harvest else self.default_moisture)
        )
        dry_matter = net_usable * (1.0 - (moisture / 100.0))

        # Availability window: Require an actual or expected harvest date or transparent fallback
        base_date = harvest.harvest_date if harvest else (crop.actual_harvest_date or crop.expected_harvest_date)
        inferred_harvest_date = False
        if not base_date:
            if config_manager.get("biomass.allow_current_date_fallback"):
                base_date = date.today()
                inferred_harvest_date = True
            else:
                raise ValidationError(
                    message=f"Cannot schedule biomass availability window: Crop '{crop.crop_type}' has no harvest date or expected harvest date.",
                    field="expected_harvest_date",
                )

        start_date = base_date + timedelta(days=1)
        end_date = start_date + timedelta(days=self.collection_window_days)

        notes = (
            f"Calculated using {crop.crop_type} RPR of {rpr:.2f} based on {grain_production:.1f}t grain. "
            f"Retained {retained_frac * 100:.0f}% for soil conservation, {competing_frac * 100:.0f}% for competing fodder. "
            f"Net usable after {self.handling_loss_frac * 100:.0f}% mechanical collection losses."
        )
        if inferred_harvest_date:
            notes += f" [Note: Harvest date was not specified; collection window estimated based on current evaluation date {base_date}.]"

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
            methodology_notes=notes,
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
                notes=f"Initial biomass estimation generated from {source}.",
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
