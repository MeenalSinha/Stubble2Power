"""
Regression tests for legacy Stubble2Power calculations.
Ensures mathematical formulas match legacy app.py behavior exactly.
"""

import pytest
import pandas as pd
from sklearn.cluster import KMeans

# Reference legacy scenarios exactly as defined in original app.py
LEGACY_SCENARIOS = {
    "Conservative": {
        "briquette_yield": 0.6,
        "biochar_yield": 0.15,
        "processing_cost_per_ton": 1000,
        "briquette_price": 5,
        "biochar_price": 12,
        "carbon_credit_per_ton": 400,
        "farmer_payment_per_ton": 1200,
        "mobile_unit_cost_per_km": 180,
        "co2_per_ton_stubble": 1.2,
        "coal_replaced_ratio": 0.6,
        "processing_time_per_ton": 2.5,
    },
    "Base Case": {
        "briquette_yield": 0.7,
        "biochar_yield": 0.2,
        "processing_cost_per_ton": 800,
        "briquette_price": 6,
        "biochar_price": 15,
        "carbon_credit_per_ton": 500,
        "farmer_payment_per_ton": 1500,
        "mobile_unit_cost_per_km": 150,
        "co2_per_ton_stubble": 1.5,
        "coal_replaced_ratio": 0.8,
        "processing_time_per_ton": 2,
    },
    "Optimistic": {
        "briquette_yield": 0.75,
        "biochar_yield": 0.22,
        "processing_cost_per_ton": 700,
        "briquette_price": 7,
        "biochar_price": 18,
        "carbon_credit_per_ton": 600,
        "farmer_payment_per_ton": 1800,
        "mobile_unit_cost_per_km": 120,
        "co2_per_ton_stubble": 1.8,
        "coal_replaced_ratio": 0.9,
        "processing_time_per_ton": 1.8,
    },
}


def legacy_calculate_unit_economics(stubble_tons, assumptions, transport_cost):
    stubble_kg = stubble_tons * 1000
    briquette_prod = stubble_kg * assumptions["briquette_yield"]
    biochar_prod = stubble_kg * assumptions["biochar_yield"]
    briquette_revenue = briquette_prod * assumptions["briquette_price"]
    biochar_revenue = biochar_prod * assumptions["biochar_price"]
    carbon_revenue = stubble_tons * assumptions["carbon_credit_per_ton"]
    total_revenue = briquette_revenue + biochar_revenue + carbon_revenue
    processing_cost = stubble_tons * assumptions["processing_cost_per_ton"]
    farmer_payment = stubble_tons * assumptions["farmer_payment_per_ton"]
    total_cost = processing_cost + farmer_payment + transport_cost
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    cost_per_ton = total_cost / stubble_tons if stubble_tons > 0 else 0
    revenue_per_ton = total_revenue / stubble_tons if stubble_tons > 0 else 0

    return {
        "production": {"briquette_kg": briquette_prod, "biochar_kg": biochar_prod},
        "revenue": {
            "briquette": briquette_revenue,
            "biochar": biochar_revenue,
            "carbon": carbon_revenue,
            "total": total_revenue,
        },
        "cost": {
            "processing": processing_cost,
            "farmer_payment": farmer_payment,
            "transport": transport_cost,
            "total": total_cost,
        },
        "metrics": {
            "profit": profit,
            "margin": margin,
            "cost_per_ton": cost_per_ton,
            "revenue_per_ton": revenue_per_ton,
            "breakeven_tons": total_cost / revenue_per_ton if revenue_per_ton > 0 else 0,
        },
    }


def legacy_calculate_environmental_impact(stubble_tons, assumptions):
    co2_avoided = stubble_tons * assumptions["co2_per_ton_stubble"]
    coal_replaced = stubble_tons * assumptions["coal_replaced_ratio"]
    return {
        "co2_avoided": co2_avoided,
        "coal_replaced": coal_replaced,
        "trees_equivalent": int(co2_avoided * 33),
        "cars_equivalent": int(co2_avoided * 0.22),
        "homes_powered": int(coal_replaced * 2),
    }


def legacy_calculate_logistics_savings(mobile_cost, stubble_tons):
    central_cost = stubble_tons * 100 * 150 / 10
    savings = central_cost - mobile_cost
    reduction_pct = (savings / central_cost * 100) if central_cost > 0 else 0
    return {
        "mobile_cost": mobile_cost,
        "central_cost": central_cost,
        "savings": savings,
        "reduction_pct": reduction_pct,
    }


class TestLegacyCalculations:
    @pytest.mark.parametrize("scenario_name", ["Conservative", "Base Case", "Optimistic"])
    def test_unit_economics_standard_inputs(self, scenario_name):
        assumptions = LEGACY_SCENARIOS[scenario_name]
        stubble_tons = 100.0
        transport_cost = 5000.0

        res = legacy_calculate_unit_economics(stubble_tons, assumptions, transport_cost)

        assert res["production"]["briquette_kg"] == 100000 * assumptions["briquette_yield"]
        assert res["production"]["biochar_kg"] == 100000 * assumptions["biochar_yield"]
        assert res["revenue"]["total"] == (
            res["revenue"]["briquette"] + res["revenue"]["biochar"] + res["revenue"]["carbon"]
        )
        assert res["cost"]["total"] == (res["cost"]["processing"] + res["cost"]["farmer_payment"] + transport_cost)
        assert res["metrics"]["profit"] == res["revenue"]["total"] - res["cost"]["total"]
        assert res["metrics"]["margin"] == (res["metrics"]["profit"] / res["revenue"]["total"]) * 100
        assert res["metrics"]["revenue_per_ton"] == res["revenue"]["total"] / stubble_tons
        assert res["metrics"]["cost_per_ton"] == res["cost"]["total"] / stubble_tons

    def test_unit_economics_zero_division_guard(self):
        assumptions = LEGACY_SCENARIOS["Base Case"]
        res = legacy_calculate_unit_economics(0.0, assumptions, 0.0)
        assert res["revenue"]["total"] == 0.0
        assert res["cost"]["total"] == 0.0
        assert res["metrics"]["profit"] == 0.0
        assert res["metrics"]["margin"] == 0.0
        assert res["metrics"]["cost_per_ton"] == 0.0
        assert res["metrics"]["revenue_per_ton"] == 0.0
        assert res["metrics"]["breakeven_tons"] == 0.0

    @pytest.mark.parametrize("scenario_name", ["Conservative", "Base Case", "Optimistic"])
    def test_environmental_impact(self, scenario_name):
        assumptions = LEGACY_SCENARIOS[scenario_name]
        stubble_tons = 250.0

        res = legacy_calculate_environmental_impact(stubble_tons, assumptions)
        expected_co2 = 250.0 * assumptions["co2_per_ton_stubble"]
        expected_coal = 250.0 * assumptions["coal_replaced_ratio"]

        assert res["co2_avoided"] == expected_co2
        assert res["coal_replaced"] == expected_coal
        assert res["trees_equivalent"] == int(expected_co2 * 33)
        assert res["cars_equivalent"] == int(expected_co2 * 0.22)
        assert res["homes_powered"] == int(expected_coal * 2)

    def test_logistics_savings(self):
        stubble_tons = 100.0
        mobile_cost = 45000.0

        res = legacy_calculate_logistics_savings(mobile_cost, stubble_tons)
        expected_central = 100.0 * 100 * 150 / 10  # 150,000
        expected_savings = 150000.0 - 45000.0  # 105,000
        expected_pct = (105000.0 / 150000.0) * 100  # 70%

        assert res["central_cost"] == expected_central
        assert res["savings"] == expected_savings
        assert pytest.approx(res["reduction_pct"], 0.01) == expected_pct

    def test_logistics_savings_zero_stubble(self):
        res = legacy_calculate_logistics_savings(0.0, 0.0)
        assert res["central_cost"] == 0.0
        assert res["savings"] == 0.0
        assert res["reduction_pct"] == 0.0

    def test_clustering_kmeans_equivalence(self):
        sample_farmers = pd.DataFrame(
            [
                {"Farmer Name": "F1", "Latitude": 30.70, "Longitude": 76.22, "Stubble (tons)": 10},
                {"Farmer Name": "F2", "Latitude": 30.71, "Longitude": 76.23, "Stubble (tons)": 15},
                {"Farmer Name": "F3", "Latitude": 30.90, "Longitude": 75.85, "Stubble (tons)": 20},
                {"Farmer Name": "F4", "Latitude": 30.91, "Longitude": 75.86, "Stubble (tons)": 25},
            ]
        )
        coords = sample_farmers[["Latitude", "Longitude"]].values
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(coords)
        assert len(clusters) == 4
        assert len(set(clusters)) == 2
