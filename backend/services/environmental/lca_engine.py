"""
Life Cycle Assessment (LCA) & Net Environmental Accounting Engine.
Implements IPCC AR6 WG1 GWP100 metrics, CEA India CO2 baseline coal displacement,
and biochar soil carbon permanence with strict separation of biogenic and fossil carbon.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.entities import EnvironmentalAssessment, DeploymentPlan, RoutePlan
from backend.schemas.environmental_lca import (
    EnvironmentalAssessmentCreate,
    EnvironmentalAssessmentResponse,
    SystemBoundarySummary
)
from backend.core.config.settings import config_manager
from backend.core.exceptions.base import NotFoundError, ValidationError
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.environmental.lca")


class LifeCycleAssessmentService:
    def __init__(self, db: Session):
        self.db = db

        # Retrieve science parameters with literature provenance
        self.burn_co2_kg = float(config_manager.get("environmental.emission_factor_burning_co2_kg_per_ton"))
        self.burn_ch4_kg = float(config_manager.get("environmental.emission_factor_burning_ch4_kg_per_ton"))
        self.burn_n2o_kg = float(config_manager.get("environmental.emission_factor_burning_n2o_kg_per_ton"))
        self.burn_pm25_kg = float(config_manager.get("environmental.emission_factor_burning_pm25_kg_per_ton"))

        self.gwp_ch4 = float(config_manager.get("environmental.gwp_ch4_ar6"))
        self.gwp_n2o = float(config_manager.get("environmental.gwp_n2o_ar6"))

        self.diesel_co2_kg_per_l = float(config_manager.get("environmental.diesel_emission_factor_kg_co2_per_liter"))
        self.coal_disp_ratio = float(config_manager.get("environmental.coal_displacement_ratio_briquette"))
        self.coal_co2_kg_per_ton = float(config_manager.get("environmental.coal_emission_factor_kg_co2_per_ton"))
        self.biochar_stable_fraction = float(config_manager.get("environmental.biochar_stable_carbon_fraction"))

    def conduct_lca(self, payload: EnvironmentalAssessmentCreate) -> EnvironmentalAssessment:
        """
        Calculates cradle-to-grave net GHG balance comparing uncontrolled open field burning
        against mobile densification, coal co-firing displacement, and biochar sequestration.
        """
        # 1. Resolve Biomass and Fuel
        deployment_plan = None
        if payload.deployment_plan_id:
            deployment_plan = self.db.scalars(
                select(DeploymentPlan).where(DeploymentPlan.id == payload.deployment_plan_id)
            ).first()

        if payload.biomass_diverted_tons is not None:
            biomass_tons = max(0.1, float(payload.biomass_diverted_tons))
        elif deployment_plan:
            biomass_tons = max(0.1, deployment_plan.total_biomass_assigned_tons)
        else:
            biomass_tons = 500.0

        # Transport and Processing Fuel (Liters)
        if payload.transport_fuel_liters is not None:
            transport_diesel_l = float(payload.transport_fuel_liters)
        elif deployment_plan:
            # Sum from actual route plans
            routes = self.db.scalars(select(RoutePlan).where(RoutePlan.deployment_plan_id == deployment_plan.id)).all()
            transport_diesel_l = sum(r.fuel_consumed_liters for r in routes)
            if transport_diesel_l <= 0:
                transport_diesel_l = deployment_plan.total_route_distance_km * 0.38
        else:
            # Rural tractor transport ~ 0.38 L/km * 35 km avg roundtrip
            transport_diesel_l = (biomass_tons / 5.0) * 12.0  # ~12 L per 5t load

        if payload.processing_fuel_liters is not None:
            proc_diesel_l = float(payload.processing_fuel_liters)
        else:
            proc_rate = float(config_manager.get("refinery.mobile.fuel_consumption_liters_per_ton"))
            proc_diesel_l = biomass_tons * proc_rate

        briquette_frac = payload.briquette_fraction_produced or 0.70
        biochar_frac = payload.biochar_fraction_produced or 0.15

        # 2. Baseline Emissions (Open Burning)
        co2_burn_tons = round((biomass_tons * self.burn_co2_kg) / 1000.0, 2)
        ch4_burn_tons = round((biomass_tons * self.burn_ch4_kg) / 1000.0, 3)
        n2o_burn_tons = round((biomass_tons * self.burn_n2o_kg) / 1000.0, 4)
        pm25_burn_tons = round((biomass_tons * self.burn_pm25_kg) / 1000.0, 3)

        # Baseline CO2e using IPCC AR6 WG1 100-year metrics
        baseline_non_co2_co2e = (ch4_burn_tons * self.gwp_ch4) + (n2o_burn_tons * self.gwp_n2o)
        baseline_total_co2e = round(co2_burn_tons + baseline_non_co2_co2e, 2)

        # 3. Project Life Cycle Emissions (Diesel Combustion)
        transport_co2_tons = round((transport_diesel_l * self.diesel_co2_kg_per_l) / 1000.0, 2)
        proc_co2_tons = round((proc_diesel_l * self.diesel_co2_kg_per_l) / 1000.0, 2)
        project_total_emissions = round(transport_co2_tons + proc_co2_tons, 2)

        # 4. Substitution and Permanence Benefits
        # Sub-bituminous coal displacement in industrial boilers
        briquettes_tons = biomass_tons * briquette_frac
        coal_displaced_tons = round(briquettes_tons * self.coal_disp_ratio, 2)
        avoided_coal_co2e_tons = round((coal_displaced_tons * self.coal_co2_kg_per_ton) / 1000.0, 2)

        # Biochar 100-Year Carbon Sequestration
        # Molecular conversion C -> CO2 is 44/12 = 3.667
        biochar_tons = biomass_tons * biochar_frac
        biochar_c_stored_tons = biochar_tons * self.biochar_stable_fraction
        biochar_co2e_stored_tons = round(biochar_c_stored_tons * (44.0 / 12.0), 2)

        # 5. Net Environmental Benefit
        # Net Benefit = Baseline Avoided - Project Emissions + Coal Displacement + Biochar Sequestration
        net_avoided_co2e = round(
            baseline_total_co2e - project_total_emissions + avoided_coal_co2e_tons + biochar_co2e_stored_tons, 2
        )
        net_benefit_ratio = round(net_avoided_co2e / max(0.01, baseline_total_co2e), 2)

        # 6. Carbon Credit Eligibility Separation
        # Verra / Gold Standard / Puro.earth carbon credit eligibility:
        # Excludes biogenic short-cycle CO2 from burning, focusing on additionality:
        # Avoided non-CO2 GHGs (CH4 + N2O) + Displaced Fossil Coal CO2 + Biochar Permanence - Fossil Project Emissions
        carbon_credit_eligible = round(
            baseline_non_co2_co2e + avoided_coal_co2e_tons + biochar_co2e_stored_tons - project_total_emissions, 2
        )
        carbon_credit_eligible = max(0.0, carbon_credit_eligible)

        assessment = EnvironmentalAssessment(
            deployment_plan_id=payload.deployment_plan_id,
            biomass_diverted_tons=round(biomass_tons, 2),
            baseline_burning_co2_tons=co2_burn_tons,
            baseline_burning_ch4_tons=ch4_burn_tons,
            baseline_burning_n2o_tons=n2o_burn_tons,
            baseline_burning_pm25_tons=pm25_burn_tons,
            baseline_total_co2e_tons=baseline_total_co2e,
            project_transport_emissions_co2_tons=transport_co2_tons,
            project_processing_emissions_co2_tons=proc_co2_tons,
            project_total_emissions_co2e_tons=project_total_emissions,
            coal_displaced_tons=coal_displaced_tons,
            avoided_coal_co2e_tons=avoided_coal_co2e_tons,
            biochar_stable_carbon_stored_co2e_tons=biochar_co2e_stored_tons,
            net_avoided_co2e_tons=net_avoided_co2e,
            net_benefit_ratio=net_benefit_ratio,
            carbon_credit_eligible_tons=carbon_credit_eligible,
            methodology_provenance="IPCC 2006 / AR6 WG1 GWP100 / CEA CO2 Baseline v19.0 / IBI Biochar Permanence",
            evidence_json={
                "gwp_metrics": {"CH4": self.gwp_ch4, "N2O": self.gwp_n2o},
                "briquettes_produced_tons": round(briquettes_tons, 2),
                "biochar_produced_tons": round(biochar_tons, 2),
                "transport_diesel_liters": round(transport_diesel_l, 1),
                "processing_diesel_liters": round(proc_diesel_l, 1),
                "pm25_avoided_tons": pm25_burn_tons
            }
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        logger.info(
            f"Conducted LCA for {biomass_tons}t biomass: Net avoided {net_avoided_co2e} tCO2e "
            f"(benefit ratio: {net_benefit_ratio}x, eligible credits: {carbon_credit_eligible} tCO2e)."
        )
        return assessment

    def get_assessment(self, assessment_id: int) -> EnvironmentalAssessment:
        ass = self.db.scalars(select(EnvironmentalAssessment).where(EnvironmentalAssessment.id == assessment_id)).first()
        if not ass:
            raise NotFoundError(message=f"Environmental assessment {assessment_id} not found.", entity="EnvironmentalAssessment")
        return ass

    def list_assessments(self) -> List[EnvironmentalAssessment]:
        return list(self.db.scalars(select(EnvironmentalAssessment).order_by(EnvironmentalAssessment.created_at.desc())).all())

    @staticmethod
    def get_system_boundary() -> SystemBoundarySummary:
        return SystemBoundarySummary()
