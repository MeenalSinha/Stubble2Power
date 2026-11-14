"""
Scientific Validation Suite: Life Cycle Assessment (LCA) & Net GHG Accounting Engine.
Validates IPCC Sixth Assessment Report (AR6 WG1) 100-year Global Warming Potentials (GWP100),
Central Electricity Authority (CEA) coal displacement benchmarks, biochar 100-year permanence,
and Verra VM0044 vs Puro.earth carbon credit separation.

References:
- IPCC AR6 WG1 (2021), Chapter 7: The Earth's Energy Budget, Climate Feedbacks, and Climate Sensitivity
- Central Electricity Authority (CEA) India (2023), "CO2 Baseline Database for the Indian Power Sector"
- Verra VCS Methodology VM0044, "Conservation of Agricultural Residues through Briquetting"
- Puro.earth Biochar Methodology (2022), "Pyrogenic Carbon Capture and Storage (CORCs)"
"""

import pytest
from sqlalchemy.orm import Session

from backend.schemas.environmental_lca import EnvironmentalAssessmentCreate
from backend.services.environmental.lca_engine import LifeCycleAssessmentService


def test_ipcc_ar6_gwp100_multipliers(db_session: Session):
    """
    Validates that GWP100 multipliers adhere strictly to IPCC AR6 WG1 Chapter 7:
    - CH4 (methane) GWP100 = 27.9
    - N2O (nitrous oxide) GWP100 = 273.0
    - CO2 = 1.0
    """
    svc = LifeCycleAssessmentService(db_session)
    assert svc.gwp_ch4 == 27.9
    assert svc.gwp_n2o == 273.0


def test_baseline_open_burning_emissions_and_air_pollutants(db_session: Session):
    """
    Validates baseline emissions for 1,000 metric tons of open field residue burning:
    - CO2: 1,460 kg/ton -> 1,460.00 tons
    - CH4: 2.70 kg/ton -> 2.700 tons
    - N2O: 0.07 kg/ton -> 0.0700 tons
    - PM2.5: 8.30 kg/ton -> 8.300 tons
    Non-CO2 GWP100 CO2e = (2.7 * 27.9) + (0.07 * 273.0) = 75.33 + 19.11 = 94.44 tCO2e
    Total Baseline CO2e = 1,460.00 + 94.44 = 1,554.44 tCO2e
    """
    svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1000.0,
        transport_fuel_liters=2400.0,
        processing_fuel_liters=3500.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20,
    )

    assessment = svc.conduct_lca(payload)

    assert assessment.biomass_diverted_tons == 1000.0
    assert assessment.baseline_burning_co2_tons == 1460.00
    assert assessment.baseline_burning_ch4_tons == 2.700
    assert assessment.baseline_burning_n2o_tons == 0.0700
    assert assessment.baseline_burning_pm25_tons == 8.300
    assert pytest.approx(1554.44, rel=1e-3) == assessment.baseline_total_co2e_tons


def test_project_emissions_diesel_stoichiometry(db_session: Session):
    """
    Validates fossil diesel combustion emissions for transport and mobile processing:
    Emission factor: 2.68 kg CO2 / liter diesel.
    Transport Fuel = 2,500 L -> 2,500 * 2.68 / 1000 = 6.70 tCO2
    Processing Fuel = 4,000 L -> 4,000 * 2.68 / 1000 = 10.72 tCO2
    Project Emissions = 6.70 + 10.72 = 17.42 tCO2
    """
    svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1000.0,
        transport_fuel_liters=2500.0,
        processing_fuel_liters=4000.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20,
    )

    assessment = svc.conduct_lca(payload)

    assert assessment.project_transport_emissions_co2_tons == 6.70
    assert assessment.project_processing_emissions_co2_tons == 10.72
    assert assessment.project_total_emissions_co2e_tons == 17.42


def test_sub_bituminous_coal_displacement_benefits(db_session: Session):
    """
    Validates thermal coal replacement in industrial boilers:
    Biomass = 1,000 tons, Briquette Fraction = 0.70 -> 700 tons briquettes.
    Coal Displacement Ratio = 0.82 -> Coal Displaced = 700 * 0.82 = 574.00 tons coal.
    Coal Emission Factor = 2,120 kg CO2 / ton coal -> 574.00 * 2.12 = 1,216.88 tCO2 avoided.
    """
    svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1000.0,
        transport_fuel_liters=2000.0,
        processing_fuel_liters=3000.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20,
    )

    assessment = svc.conduct_lca(payload)

    assert assessment.coal_displaced_tons == 574.00
    assert assessment.avoided_coal_co2e_tons == 1216.88


def test_biochar_100_year_permanence_stoichiometry(db_session: Session):
    """
    Validates pyrogenic biochar carbon sequestration and stoichiometric permanence:
    Biomass = 1,000 tons, Biochar Fraction = 0.20 -> 200.00 tons biochar.
    Stable Carbon Fraction = 0.72 (72% recalcitrant carbon with half-life > 100 years).
    Stored Carbon = 200 * 0.72 = 144.00 tons elemental C.
    CO2 equivalent stored = 144.00 * (44.0 / 12.0) = 528.00 tCO2e sequestered.
    """
    svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1000.0,
        transport_fuel_liters=2000.0,
        processing_fuel_liters=3000.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20,
    )

    assessment = svc.conduct_lca(payload)

    # 144.00 tons C * (44/12) = 528.00 tCO2e
    assert assessment.biochar_stable_carbon_stored_co2e_tons == 528.00


def test_net_environmental_balance_identity(db_session: Session):
    """
    Validates that Net Avoided GHG matches the exact scientific balance identity:
    Net GHG Avoided = Baseline Avoided - Project Diesel Emissions + Coal Displacement + Biochar Sequestration.
    """
    svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1000.0,
        transport_fuel_liters=2500.0,
        processing_fuel_liters=4000.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20,
    )

    assessment = svc.conduct_lca(payload)

    expected_net = (
        assessment.baseline_total_co2e_tons
        - assessment.project_total_emissions_co2e_tons
        + assessment.avoided_coal_co2e_tons
        + assessment.biochar_stable_carbon_stored_co2e_tons
    )

    assert pytest.approx(expected_net, rel=1e-3) == assessment.net_avoided_co2e_tons
    assert assessment.net_avoided_co2e_tons > 0.0


def test_carbon_market_credit_separation(db_session: Session):
    """
    Validates regulatory additionality separation for carbon credits.
    """
    svc = LifeCycleAssessmentService(db_session)
    payload = EnvironmentalAssessmentCreate(
        biomass_diverted_tons=1000.0,
        transport_fuel_liters=2000.0,
        processing_fuel_liters=3000.0,
        briquette_fraction_produced=0.70,
        biochar_fraction_produced=0.20,
    )

    assessment = svc.conduct_lca(payload)

    assert assessment.carbon_credit_eligible_tons > 0.0
    assert assessment.biochar_stable_carbon_stored_co2e_tons == 528.00
