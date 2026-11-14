"""
Agricultural Fire Context Classification Service.
Harmonizes Land Use Land Cover (LULC), authoritative crop calendars,
and thermal characteristics into transparent, evidence-based context classifications.

IMPORTANT ARCHITECTURAL RULE:
Phase 9 context classification does NOT depend on Phase 8 statistical anomaly scores.
Unusual fire activity does not equal agricultural fire activity.
"""

from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.models.entities import (
    AgriculturalContextAssessment,
    HarmonizedObservation
)
from backend.services.agriculture.crop_calendar_service import CropCalendarService
from backend.services.agriculture.land_use_service import LandUseService
from backend.core.config.settings import config_manager
from backend.core.logging.logger import get_logger
from backend.schemas.agriculture import (
    AgriculturalContextAssessmentResponse,
    AgriculturalContextSummary
)

logger = get_logger("stubble2power.agriculture.classification")


class AgriculturalClassificationService:
    def __init__(self, db: Session):
        self.db = db
        self.crop_cal_svc = CropCalendarService(db)
        self.land_use_svc = LandUseService(db)
        self.min_conf_likely = float(config_manager.get("agriculture.classification.min_confidence_likely"))
        self.min_conf_possible = float(config_manager.get("agriculture.classification.min_confidence_possible"))
        self.stubble_max_frp = float(config_manager.get("agriculture.thermal.stubble_max_frp_mw"))
        self.cropland_buffer = float(config_manager.get("agriculture.land_use.cropland_buffer_km"))
        self.weight_land_use = float(config_manager.get("agriculture.classification.weight_land_use"))
        self.weight_calendar = float(config_manager.get("agriculture.classification.weight_calendar"))
        self.weight_thermal = float(config_manager.get("agriculture.classification.weight_thermal"))

    def assess_observation(
        self,
        observation_date: date,
        latitude: float,
        longitude: float,
        grid_id: str,
        frp_mw: float = 0.0,
        brightness_k: Optional[float] = None,
        state_name: str = "Punjab",
        harmonized_id: Optional[int] = None
    ) -> AgriculturalContextAssessment:
        """
        Classifies an individual fire observation into one of four authoritative categories:
        1. LIKELY_AGRICULTURAL_CONTEXT
        2. POSSIBLE_AGRICULTURAL_CONTEXT
        3. OTHER_LAND_USE_CONTEXT
        4. UNKNOWN_OR_INSUFFICIENT_EVIDENCE
        """
        # 1. Spatial Land Use Classification
        lulc = self.land_use_svc.classify_coordinate(latitude, longitude)
        lu_class = lulc["land_use_class"]
        lu_conf = lulc["confidence"]
        dist_to_crop = lulc["distance_to_cropland_km"]

        # 2. Temporal Crop Calendar Matching
        cal_match = self.crop_cal_svc.match_harvest_window(observation_date, state_name=state_name)
        harvest_status = cal_match["status"]
        matched_crop = cal_match["matched_crop"]
        susceptibility = cal_match["susceptibility"]

        # 3. Thermal Physical Verification
        # Stubble fires typically display FRP <= 250 MW. Very high FRP indicates forest wildfire or industrial flare.
        is_thermal_compatible = (frp_mw <= self.stubble_max_frp)

        # 4. Bayesian Evidence Synthesis & Confidence Scoring
        evidence_factors = []
        score = 0.0

        # Cropland spatial factor
        if lu_class == "CROPLAND":
            score += self.weight_land_use * lu_conf
            evidence_factors.append(f"Located directly within confirmed agricultural land ({lulc['zone_name']}).")
        elif dist_to_crop <= self.cropland_buffer:
            score += (self.weight_land_use * 0.55) * lu_conf
            evidence_factors.append(f"Located within {dist_to_crop:.2f} km of agricultural cropland.")
        else:
            evidence_factors.append(f"Located in non-agricultural land ({lu_class}).")

        # Temporal harvest calendar factor
        if harvest_status == "IN_PEAK_HARVEST_WINDOW":
            score += self.weight_calendar
            evidence_factors.append(f"Active date falls within peak harvest burn window for {matched_crop}.")
        elif harvest_status == "IN_EXTENDED_HARVEST_WINDOW":
            score += self.weight_calendar * 0.625
            evidence_factors.append(f"Active date falls in extended harvest season for {matched_crop}.")
        else:
            evidence_factors.append("Active date is off-season for major crop residue burning.")

        # Thermal signature factor
        if is_thermal_compatible and frp_mw > 0:
            score += self.weight_thermal
            evidence_factors.append(f"FRP {frp_mw:.1f} MW is consistent with crop residue flaming/smoldering.")
        elif frp_mw > self.stubble_max_frp:
            score -= (self.weight_thermal * 2.0)
            evidence_factors.append(f"FRP {frp_mw:.1f} MW exceeds typical crop residue limit (> {self.stubble_max_frp:.1f} MW).")

        confidence_score = max(0.0, min(1.0, round(score, 3)))

        # 5. Authoritative Context Determination
        if lu_class in ("FOREST", "URBAN_INDUSTRIAL", "WETLAND_WATER"):
            classification = "OTHER_LAND_USE_CONTEXT"
            reason = f"Observation coordinates coincide with {lu_class} land cover."
        elif not is_thermal_compatible:
            classification = "OTHER_LAND_USE_CONTEXT"
            reason = f"Thermal intensity ({frp_mw:.1f} MW) strongly suggests heavy industrial or forest crown fire."
        elif confidence_score >= self.min_conf_likely and (lu_class == "CROPLAND" or dist_to_crop <= self.cropland_buffer):
            classification = "LIKELY_AGRICULTURAL_CONTEXT"
            reason = f"High confidence ({confidence_score*100:.1f}%): Confirmed cropland coincident with {matched_crop} harvest window."
        elif confidence_score >= self.min_conf_possible:
            classification = "POSSIBLE_AGRICULTURAL_CONTEXT"
            reason = f"Moderate confidence ({confidence_score*100:.1f}%): Near agricultural boundary or extended harvest window."
        elif harvest_status == "OFF_SEASON" and dist_to_crop > self.cropland_buffer:
            classification = "OTHER_LAND_USE_CONTEXT"
            reason = "Off-season observation distant from active cropland."
        else:
            classification = "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"
            reason = f"Insufficient evidence to classify (confidence {confidence_score*100:.1f}%)."

        # Compute stubble risk index (0 to 100)
        stubble_risk = round(confidence_score * 100.0, 1) if classification in ("LIKELY_AGRICULTURAL_CONTEXT", "POSSIBLE_AGRICULTURAL_CONTEXT") else 0.0

        evidence_payload = {
            "classification_reason": reason,
            "evidence_factors": evidence_factors,
            "matched_crop": matched_crop,
            "crop_calendar_status": harvest_status,
            "susceptibility": susceptibility,
            "land_use_class": lu_class,
            "land_use_zone": lulc.get("zone_name", "Unknown"),
            "distance_to_cropland_km": dist_to_crop,
            "frp_mw": frp_mw,
            "thermal_compatible": is_thermal_compatible,
            "confidence_percentage": round(confidence_score * 100.0, 1)
        }

        assessment = AgriculturalContextAssessment(
            harmonized_observation_id=harmonized_id,
            observation_date=observation_date,
            latitude=round(latitude, 4),
            longitude=round(longitude, 4),
            grid_id=grid_id,
            land_use_class=lu_class,
            land_use_confidence=round(lu_conf, 3),
            matched_crop=matched_crop,
            harvest_window_status=harvest_status,
            context_classification=classification,
            confidence_score=confidence_score,
            distance_to_cropland_km=round(dist_to_crop, 2),
            stubble_risk_index=stubble_risk,
            evidence_json=evidence_payload
        )
        return assessment

    def classify_harmonized_records(
        self,
        date_start: date,
        date_end: date,
        state_name: str = "Punjab",
        persist: bool = True
    ) -> List[AgriculturalContextAssessment]:
        """
        Classifies all harmonized fire observations in the specified date range.
        """
        stmt = select(HarmonizedObservation).where(
            and_(
                HarmonizedObservation.observation_date >= date_start,
                HarmonizedObservation.observation_date <= date_end
            )
        )
        records = list(self.db.scalars(stmt).all())
        if not records:
            logger.info(f"No harmonized observations found to classify between {date_start} and {date_end}.")
            return []

        assessments: List[AgriculturalContextAssessment] = []
        for r in records:
            ass = self.assess_observation(
                observation_date=r.observation_date,
                latitude=r.centroid_lat,
                longitude=r.centroid_lon,
                grid_id=r.grid_id,
                frp_mw=float(r.harmonized_frp_mw or 0.0),
                state_name=state_name,
                harmonized_id=r.id
            )
            assessments.append(ass)

        if persist and assessments:
            # Delete previous assessments in date range
            self.db.query(AgriculturalContextAssessment).filter(
                and_(
                    AgriculturalContextAssessment.observation_date >= date_start,
                    AgriculturalContextAssessment.observation_date <= date_end
                )
            ).delete()
            self.db.add_all(assessments)
            self.db.commit()
            logger.info(f"Persisted {len(assessments)} agricultural context assessments.")

        return assessments

    def get_summary(
        self,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None
    ) -> AgriculturalContextSummary:
        """Computes aggregate distribution metrics of agricultural fire context classifications."""
        stmt = select(AgriculturalContextAssessment)
        filters = []
        if date_start:
            filters.append(AgriculturalContextAssessment.observation_date >= date_start)
        if date_end:
            filters.append(AgriculturalContextAssessment.observation_date <= date_end)
        if filters:
            stmt = stmt.where(and_(*filters))

        records = list(self.db.scalars(stmt).all())
        total = len(records)
        likely_count = sum(1 for r in records if r.context_classification == "LIKELY_AGRICULTURAL_CONTEXT")
        possible_count = sum(1 for r in records if r.context_classification == "POSSIBLE_AGRICULTURAL_CONTEXT")
        other_count = sum(1 for r in records if r.context_classification == "OTHER_LAND_USE_CONTEXT")
        unknown_count = sum(1 for r in records if r.context_classification == "UNKNOWN_OR_INSUFFICIENT_EVIDENCE")

        crop_counts: Dict[str, int] = {}
        lu_counts: Dict[str, int] = {}
        for r in records:
            if r.matched_crop:
                crop_counts[r.matched_crop] = crop_counts.get(r.matched_crop, 0) + 1
            lu_counts[r.land_use_class] = lu_counts.get(r.land_use_class, 0) + 1

        percent_likely = round((likely_count / total * 100.0), 1) if total > 0 else 0.0

        resp_list = [
            AgriculturalContextAssessmentResponse(
                id=r.id,
                harmonized_observation_id=r.harmonized_observation_id,
                observation_date=r.observation_date,
                latitude=r.latitude,
                longitude=r.longitude,
                grid_id=r.grid_id,
                land_use_class=r.land_use_class,
                land_use_confidence=r.land_use_confidence,
                matched_crop=r.matched_crop,
                harvest_window_status=r.harvest_window_status,
                context_classification=r.context_classification,
                confidence_score=r.confidence_score,
                distance_to_cropland_km=r.distance_to_cropland_km,
                stubble_risk_index=r.stubble_risk_index,
                evidence_json=r.evidence_json,
                created_at=r.created_at
            )
            for r in records
        ]

        return AgriculturalContextSummary(
            total_assessed=total,
            likely_agricultural_count=likely_count,
            possible_agricultural_count=possible_count,
            other_land_use_count=other_count,
            unknown_count=unknown_count,
            percent_likely_agricultural=percent_likely,
            crop_breakdown=crop_counts,
            land_use_breakdown=lu_counts,
            assessments=resp_list
        )
