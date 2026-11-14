"""
Pydantic Schemas for Life Cycle Assessment (LCA) and Net Environmental Accounting.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class EnvironmentalAssessmentCreate(BaseModel):
    deployment_plan_id: Optional[int] = None
    biomass_diverted_tons: Optional[float] = None
    transport_fuel_liters: Optional[float] = None
    processing_fuel_liters: Optional[float] = None
    biochar_fraction_produced: Optional[float] = 0.15
    briquette_fraction_produced: Optional[float] = 0.70


class EnvironmentalAssessmentResponse(BaseModel):
    id: int
    deployment_plan_id: Optional[int] = None
    biomass_diverted_tons: float
    baseline_burning_co2_tons: float
    baseline_burning_ch4_tons: float
    baseline_burning_n2o_tons: float
    baseline_burning_pm25_tons: float
    baseline_total_co2e_tons: float
    project_transport_emissions_co2_tons: float
    project_processing_emissions_co2_tons: float
    project_total_emissions_co2e_tons: float
    coal_displaced_tons: float
    avoided_coal_co2e_tons: float
    biochar_stable_carbon_stored_co2e_tons: float
    net_avoided_co2e_tons: float
    net_benefit_ratio: float
    carbon_credit_eligible_tons: float
    methodology_provenance: str
    evidence_json: Dict[str, Any] = {}
    created_at: datetime


class SystemBoundarySummary(BaseModel):
    baseline_pathway: str = "Uncontrolled Open-Field Agricultural Burning"
    project_pathways: List[str] = [
        "In-Field Mobile Collection & Mechanical Baling",
        "Rural Road Low-Emission Tractor Transport",
        "Decentralized Briquetting & Biochar Pyrolysis",
        "Industrial Sub-Bituminous Coal Displacement",
        "100-Year Soil Carbon Sequestration via Biochar",
    ]
    gwp_version: str = "IPCC AR6 WG1 100-year metrics (CH4=27.9, N2O=273)"
    grid_emission_factor_source: str = "CEA CO2 Baseline Database for the Indian Power Sector v19.0"
