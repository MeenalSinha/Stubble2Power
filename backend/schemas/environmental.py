"""
Pydantic schemas for Environmental and Social Impact.
"""

from pydantic import BaseModel, Field


class EnvironmentalImpactResult(BaseModel):
    stubble_tons: float
    co2_avoided: float = Field(..., description="Avoided CO2 emissions in metric tons")
    coal_replaced: float = Field(..., description="Thermal coal equivalent replaced in metric tons")
    trees_equivalent: int = Field(..., description="Equivalent tree seedlings growing for 10 years")
    cars_equivalent: int = Field(..., description="Equivalent annual passenger vehicle emissions avoided")
    homes_powered: int = Field(..., description="Equivalent households powered annually")
