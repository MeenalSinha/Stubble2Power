"""
Environmental and Social Impact Service.
Transforms agricultural residue prevention into standardized climate and emissions metrics.
"""

from typing import Dict, Optional
from backend.core.config.settings import config_manager
from backend.schemas.environmental import EnvironmentalImpactResult


class EnvironmentalService:
    @staticmethod
    def calculate_environmental_impact(
        stubble_tons: float,
        assumptions: Optional[Dict[str, float]] = None,
        scenario_name: str = "Base Case"
    ) -> EnvironmentalImpactResult:
        """
        Calculates avoided CO2 emissions, coal replacement equivalents, and EPA social indicators.
        """
        if assumptions is None:
            assumptions = config_manager.get_scenario_assumptions(scenario_name)

        stubble_tons = max(0.0, float(stubble_tons))

        co2_factor = float(assumptions.get("co2_per_ton_stubble", 1.50))
        coal_factor = float(assumptions.get("coal_replaced_ratio", 0.80))

        trees_per_ton_co2 = float(config_manager.get("environmental.equivalents.trees_per_ton_co2"))
        cars_per_ton_co2 = float(config_manager.get("environmental.equivalents.cars_per_ton_co2"))
        homes_per_ton_coal = float(config_manager.get("environmental.equivalents.homes_powered_per_ton_coal"))

        co2_avoided = stubble_tons * co2_factor
        coal_replaced = stubble_tons * coal_factor

        return EnvironmentalImpactResult(
            stubble_tons=stubble_tons,
            co2_avoided=co2_avoided,
            coal_replaced=coal_replaced,
            trees_equivalent=int(co2_avoided * trees_per_ton_co2),
            cars_equivalent=int(co2_avoided * cars_per_ton_co2),
            homes_powered=int(coal_replaced * homes_per_ton_coal)
        )
