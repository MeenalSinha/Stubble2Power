"""
Biomass Inventory & Commitment Management Service.
Tracks agricultural residue lifecycle stages (ESTIMATED, CONFIRMED, COMMITTED,
COLLECTED, STORED, ALLOCATED, PROCESSED) and ensures zero double-allocation.
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from backend.models.entities import BiomassEstimate, BiomassInventoryTransaction, Farm, FarmCrop
from backend.core.exceptions.base import ValidationError, NotFoundError
from backend.core.logging.logger import get_logger
from backend.schemas.biomass import BiomassInventoryTransactionCreate, BiomassAvailabilitySummary

logger = get_logger("stubble2power.biomass.inventory")


class BiomassInventoryService:
    VALID_STAGES = ["ESTIMATED", "CONFIRMED", "COMMITTED", "COLLECTED", "STORED", "ALLOCATED", "PROCESSED"]

    def __init__(self, db: Session):
        self.db = db

    def record_transaction(
        self,
        payload_or_biomass_id: Any = None,
        farm_id: Optional[int] = None,
        stage: Optional[str] = None,
        quantity_tons: Optional[float] = None,
        allocated_unit_id: Optional[int] = None,
        notes: Optional[str] = None,
        **kwargs
    ) -> BiomassInventoryTransaction:
        """Transitions biomass quantity through an audited lifecycle stage."""
        if isinstance(payload_or_biomass_id, BiomassInventoryTransactionCreate):
            payload = payload_or_biomass_id
        else:
            est_id = payload_or_biomass_id if isinstance(payload_or_biomass_id, int) else kwargs.get("biomass_estimate_id")
            payload = BiomassInventoryTransactionCreate(
                biomass_estimate_id=est_id,
                farm_id=farm_id or kwargs.get("farm_id"),
                stage=stage or kwargs.get("stage", "ALLOCATED"),
                quantity_tons=quantity_tons if quantity_tons is not None else kwargs.get("quantity_tons", 0.0),
                allocated_unit_id=allocated_unit_id or kwargs.get("allocated_unit_id"),
                notes=notes or kwargs.get("notes")
            )

        stage_str = payload.stage.upper()
        if stage_str not in self.VALID_STAGES:
            raise ValidationError(
                message=f"Invalid inventory stage '{stage_str}'. Must be one of {self.VALID_STAGES}.",
                field="stage"
            )

        estimate = self.db.scalars(select(BiomassEstimate).where(BiomassEstimate.id == payload.biomass_estimate_id)).first()
        if not estimate:
            raise NotFoundError(message=f"Biomass estimate {payload.biomass_estimate_id} not found.", entity="BiomassEstimate")

        # Double allocation prevention check
        if stage_str in ("ALLOCATED", "COMMITTED"):
            existing_allocated = self.db.query(func.sum(BiomassInventoryTransaction.quantity_tons)).filter(
                and_(
                    BiomassInventoryTransaction.biomass_estimate_id == payload.biomass_estimate_id,
                    BiomassInventoryTransaction.stage == "ALLOCATED"
                )
            ).scalar() or 0.0

            if (existing_allocated + payload.quantity_tons) > estimate.net_usable_biomass_tons:
                raise ValidationError(
                    message=(
                        f"Cannot allocate {payload.quantity_tons:.1f}t. Total allocated ({existing_allocated + payload.quantity_tons:.1f}t) "
                        f"would exceed net usable biomass ({estimate.net_usable_biomass_tons:.1f}t)."
                    ),
                    field="quantity_tons"
                )

        tx = BiomassInventoryTransaction(
            biomass_estimate_id=payload.biomass_estimate_id,
            farm_id=payload.farm_id,
            quantity_tons=round(payload.quantity_tons, 2),
            stage=stage_str,
            allocated_unit_id=payload.allocated_unit_id,
            transaction_timestamp=datetime.utcnow(),
            notes=payload.notes
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        logger.info(f"Recorded inventory transaction #{tx.id}: {tx.quantity_tons}t transitioned to '{stage}'.")
        return tx

    def get_availability_summary(
        self,
        district: Optional[str] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None
    ) -> BiomassAvailabilitySummary:
        """Computes reconciled inventory statistics across all registered farms."""
        stmt = select(BiomassEstimate, Farm, FarmCrop).join(FarmCrop, BiomassEstimate.farm_crop_id == FarmCrop.id).join(Farm, FarmCrop.farm_id == Farm.id)

        filters = []
        if district:
            filters.append(Farm.district == district)
        if date_start:
            filters.append(BiomassEstimate.availability_start_date >= date_start)
        if date_end:
            filters.append(BiomassEstimate.availability_end_date <= date_end)
        if filters:
            stmt = stmt.where(and_(*filters))

        rows = self.db.execute(stmt).all()

        tot_gross = sum(r[0].gross_residue_tons for r in rows)
        tot_retained = sum(r[0].retained_residue_tons for r in rows)
        tot_competing = sum(r[0].competing_demand_tons for r in rows)
        tot_collectable = sum(r[0].collectable_residue_tons for r in rows)
        tot_usable = sum(r[0].net_usable_biomass_tons for r in rows)

        crop_map: Dict[str, float] = {}
        dist_map: Dict[str, float] = {}
        estimate_ids = [r[0].id for r in rows]

        for r in rows:
            crop_name = r[2].crop_type
            crop_map[crop_name] = round(crop_map.get(crop_name, 0.0) + r[0].net_usable_biomass_tons, 1)
            dist_name = r[1].district
            dist_map[dist_name] = round(dist_map.get(dist_name, 0.0) + r[0].net_usable_biomass_tons, 1)

        # Query committed and processed transactions
        committed = 0.0
        processed = 0.0
        if estimate_ids:
            tx_stmt = select(BiomassInventoryTransaction.stage, func.sum(BiomassInventoryTransaction.quantity_tons)).where(
                BiomassInventoryTransaction.biomass_estimate_id.in_(estimate_ids)
            ).group_by(BiomassInventoryTransaction.stage)
            tx_res = self.db.execute(tx_stmt).all()
            for stage, qty in tx_res:
                if stage in ("COMMITTED", "ALLOCATED"):
                    committed += float(qty or 0.0)
                elif stage == "PROCESSED":
                    processed += float(qty or 0.0)

        unallocated = max(0.0, tot_usable - committed)

        return BiomassAvailabilitySummary(
            total_gross_residue_tons=round(tot_gross, 1),
            total_retained_soil_tons=round(tot_retained, 1),
            total_competing_fodder_tons=round(tot_competing, 1),
            total_collectable_tons=round(tot_collectable, 1),
            total_net_usable_tons=round(tot_usable, 1),
            confirmed_available_tons=round(tot_usable, 1),
            committed_to_processing_tons=round(committed, 1),
            processed_tons=round(processed, 1),
            unallocated_usable_tons=round(unallocated, 1),
            crop_wise_summary=crop_map,
            district_wise_summary=dist_map
        )

    def get_regional_availability_summary(self, region: Optional[str] = None) -> BiomassAvailabilitySummary:
        return self.get_availability_summary(district=region)

    def list_transactions_by_farm(self, farm_id: int) -> List[BiomassInventoryTransaction]:
        return list(
            self.db.scalars(
                select(BiomassInventoryTransaction)
                .where(BiomassInventoryTransaction.farm_id == farm_id)
                .order_by(BiomassInventoryTransaction.transaction_timestamp.desc())
            ).all()
        )
