"""
Unit tests for configuration architecture and geospatial calculations.
"""

import pytest
from backend.core.config.settings import ConfigManager
from backend.core.exceptions.base import ConfigurationError, ValidationError
from backend.services.geospatial.service import GeospatialService


class TestConfigManager:
    def test_get_valid_parameter(self):
        cm = ConfigManager()
        val = cm.get("scenario.base_case.briquette_price")
        assert val == 6.0
        meta = cm.get_metadata("scenario.base_case.briquette_price")
        assert meta.unit == "INR/kg"
        assert meta.source != ""
        assert meta.effective_date != ""

    def test_missing_parameter_raises_config_error(self):
        cm = ConfigManager()
        with pytest.raises(ConfigurationError):
            cm.get("non_existent_key_123")

    def test_validation_bounds_enforced(self):
        cm = ConfigManager()
        # Out-of-bounds update should fail
        with pytest.raises(ConfigurationError):
            cm.set("scenario.base_case.briquette_yield", 1.5)  # Max is 0.9

    def test_scenario_assumptions_extraction(self):
        cm = ConfigManager()
        base = cm.get_scenario_assumptions("Base Case")
        assert "briquette_yield" in base
        assert base["briquette_yield"] == 0.7
        assert "biochar_yield" in base
        assert base["biochar_yield"] == 0.2


class TestGeospatialService:
    def test_haversine_distance_known_points(self):
        # Distance between Ludhiana (30.9010, 75.8573) and Chandigarh (30.7333, 76.7794) is ~91-95 km
        dist = GeospatialService.haversine_distance(30.9010, 75.8573, 30.7333, 76.7794)
        assert 88.0 <= dist <= 96.0

    def test_haversine_same_point(self):
        dist = GeospatialService.haversine_distance(30.0, 75.0, 30.0, 75.0)
        assert dist == 0.0

    def test_coordinate_validation(self):
        GeospatialService.validate_coordinates(30.0, 75.0)  # valid
        with pytest.raises(ValidationError):
            GeospatialService.validate_coordinates(95.0, 75.0)  # invalid lat
        with pytest.raises(ValidationError):
            GeospatialService.validate_coordinates(30.0, 195.0)  # invalid lon

    def test_grid_id_computation(self):
        grid_id = GeospatialService.compute_grid_id(30.723, 76.812, 0.05)
        assert grid_id.startswith("grid_")
        center_lat, center_lon = GeospatialService.get_grid_cell_center(grid_id, 0.05)
        assert abs(center_lat - 30.725) < 0.01
