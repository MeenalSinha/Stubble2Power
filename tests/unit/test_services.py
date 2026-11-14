"""
Unit tests for Economics, Environmental, Clustering, and Quality Control services.
"""

import pytest
import pandas as pd
from backend.services.economics.service import EconomicsService
from backend.services.environmental.service import EnvironmentalService
from backend.services.clustering.service import ClusteringService
from backend.services.fire.quality_service import QualityControlService


class TestEconomicsService:
    def test_calculate_unit_economics_positive(self):
        result = EconomicsService.calculate_unit_economics(
            stubble_tons=100.0,
            transport_cost=5000.0,
            scenario_name="Base Case"
        )
        assert result.stubble_tons == 100.0
        assert result.production.briquette_kg == 70000.0
        assert result.production.biochar_kg == 20000.0
        assert result.revenue.total == 770000.0
        assert result.cost.total == 235000.0
        assert result.metrics.profit == 535000.0
        assert pytest.approx(result.metrics.margin, 0.01) == 69.48

    def test_calculate_unit_economics_zero(self):
        result = EconomicsService.calculate_unit_economics(stubble_tons=0.0, transport_cost=0.0)
        assert result.metrics.profit == 0.0
        assert result.metrics.cost_per_ton == 0.0
        assert result.metrics.breakeven_tons == 0.0

    def test_calculate_logistics_savings(self):
        res = EconomicsService.calculate_logistics_savings(mobile_cost=5000.0, stubble_tons=100.0)
        assert res.central_cost == 150000.0
        assert res.savings == 145000.0
        assert pytest.approx(res.reduction_pct, 0.01) == 96.67


class TestEnvironmentalService:
    def test_environmental_impact(self):
        res = EnvironmentalService.calculate_environmental_impact(100.0, scenario_name="Base Case")
        assert res.co2_avoided == 150.0
        assert res.coal_replaced == 80.0
        assert res.trees_equivalent == int(150.0 * 33)
        assert res.cars_equivalent == int(150.0 * 0.22)
        assert res.homes_powered == int(80.0 * 2)


class TestClusteringService:
    def test_clustering_execution(self):
        df = pd.DataFrame([
            {'Farmer Name': 'F1', 'Village': 'V1', 'District': 'D1', 'Latitude': 30.70, 'Longitude': 76.22, 'Stubble (tons)': 10.0},
            {'Farmer Name': 'F2', 'Village': 'V1', 'District': 'D1', 'Latitude': 30.72, 'Longitude': 76.24, 'Stubble (tons)': 12.0},
            {'Farmer Name': 'F3', 'Village': 'V2', 'District': 'D2', 'Latitude': 30.90, 'Longitude': 75.85, 'Stubble (tons)': 20.0},
            {'Farmer Name': 'F4', 'Village': 'V2', 'District': 'D2', 'Latitude': 30.92, 'Longitude': 75.87, 'Stubble (tons)': 25.0},
        ])
        res = ClusteringService.generate_clusters(farmers_df=df, n_clusters=2)
        assert res.total_farmers == 4
        assert res.total_stubble_tons == 67.0
        assert len(res.cluster_metrics) == 2
        assert len(res.assigned_points) == 4
        assert res.total_mobile_transport_cost_inr >= 0


class TestQualityControlService:
    def test_modis_normalization(self):
        raw = {
            "latitude": 30.85,
            "longitude": 75.40,
            "brightness": 325.5,
            "scan": 1.2,
            "track": 1.1,
            "acq_date": "2025-10-25",
            "acq_time": "0830",
            "satellite": "Aqua",
            "confidence": "85",
            "version": "6.1NRT",
            "bright_t31": 298.0,
            "frp": 45.2,
            "daynight": "D",
            "_instrument": "MODIS"
        }
        norm = QualityControlService.process_raw_record(raw)
        assert norm.is_valid is True
        assert norm.instrument == "MODIS"
        assert norm.confidence_normalized == 0.85
        assert norm.acquisition_time_utc == "08:30"
        assert norm.frp == 45.2
        assert norm.spatial_grid_id.startswith("grid_")

    def test_viirs_normalization(self):
        raw = {
            "latitude": 30.85,
            "longitude": 75.40,
            "bright_ti4": 340.2,
            "scan": 0.4,
            "track": 0.35,
            "acq_date": "2025-10-25",
            "acq_time": "0835",
            "satellite": "NOAA-20",
            "confidence": "nominal",
            "version": "2.0NRT",
            "bright_ti5": 301.0,
            "frp": 12.8,
            "daynight": "D",
            "_instrument": "VIIRS"
        }
        norm = QualityControlService.process_raw_record(raw)
        assert norm.is_valid is True
        assert norm.instrument == "VIIRS"
        assert norm.confidence_normalized == 0.7  # nominal -> 0.7

    def test_quarantine_invalid_coordinates(self):
        raw = {
            "latitude": 130.85,  # Out of range
            "longitude": 75.40,
            "acq_date": "2025-10-25",
            "acq_time": "0830",
            "confidence": "50",
            "_instrument": "MODIS"
        }
        norm = QualityControlService.process_raw_record(raw)
        assert norm.is_valid is False
        assert "Invalid coordinates" in norm.quarantine_reason
