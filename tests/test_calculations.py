"""
Unit Tests for EcoPulse Carbon Calculation Engine
Tests input validation, mathematical conversion logic, benchmarks, and recommendations.
"""

import pytest
from calculations import (
    validate_metric_input,
    calculate_transportation_emissions,
    calculate_home_energy_emissions,
    calculate_waste_emissions,
    calculate_other_emissions,
    calculate_total_footprint,
    generate_recommendations
)
from config import Config

def test_validate_metric_input_valid():
    """Verify that valid inputs pass validation and are properly cleaned."""
    raw = {
        "vehicle_miles_per_week": "150",
        "vehicle_mpg": "28",
        "vehicle_maintenance": "true",
        "transit_miles_per_week": "30",
        "flights_per_year": "2",
        "electricity_kwh_per_month": "400",
        "clean_energy_pct": "20",
        "heating_units_per_month": "25",
        "waste_bags_per_week": "2",
        "recycling_habit": "regularly",
        "composting_habit": "1",
        "diet_habit": "vegetarian",
        "shopping_habit": "minimalist",
        "reusable_habit": "yes"
    }
    is_valid, errors, cleaned = validate_metric_input(raw)
    assert is_valid is True
    assert len(errors) == 0
    assert cleaned["vehicle_miles_per_week"] == 150.0
    assert cleaned["vehicle_mpg"] == 28.0
    assert cleaned["vehicle_maintenance"] is True
    assert cleaned["composting_habit"] is True
    assert cleaned["diet_habit"] == "vegetarian"

def test_validate_metric_input_negative_and_malformed():
    """Verify that negative and malformed values are rejected with clear error messages."""
    raw = {
        "vehicle_miles_per_week": "-50",
        "vehicle_mpg": "not_a_number",
        "clean_energy_pct": "150"
    }
    is_valid, errors, cleaned = validate_metric_input(raw)
    assert is_valid is False
    assert "vehicle_miles_per_week" in errors
    assert "vehicle_mpg" in errors
    assert "clean_energy_pct" in errors

def test_transportation_calculation():
    """Verify transportation emissions formula and maintenance factor."""
    data_maintained = {
        "vehicle_miles_per_week": 200.0,
        "vehicle_mpg": 25.0,
        "vehicle_maintenance": True,
        "transit_miles_per_week": 0.0,
        "flights_per_year": 0.0
    }
    data_unmaintained = dict(data_maintained, vehicle_maintenance=False)

    emissions_m = calculate_transportation_emissions(data_maintained)
    emissions_u = calculate_transportation_emissions(data_unmaintained)

    # Weekly gallons = 200 / 25 = 8. Annual = 8 * 52 = 416.
    # Unmaintained = 416 * 8.887 = 3696.99 kg
    # Maintained = 3696.99 * 0.96 = 3549.11 kg
    assert pytest.approx(emissions_u, rel=1e-2) == 3696.99
    assert pytest.approx(emissions_m, rel=1e-2) == 3549.11
    assert emissions_m < emissions_u

def test_home_energy_calculation_clean_energy():
    """Verify home energy emissions decrease proportionally with clean energy."""
    base_data = {
        "electricity_kwh_per_month": 500.0,
        "clean_energy_pct": 0.0,
        "heating_units_per_month": 0.0
    }
    clean_data = dict(base_data, clean_energy_pct=50.0)

    e_base = calculate_home_energy_emissions(base_data)
    e_clean = calculate_home_energy_emissions(clean_data)

    assert pytest.approx(e_clean * 2, rel=1e-2) == e_base

def test_waste_composting_discount():
    """Verify composting diverts methane and reduces net waste emissions."""
    no_compost = {
        "waste_bags_per_week": 2.0,
        "recycling_habit": "regularly",
        "composting_habit": False
    }
    with_compost = dict(no_compost, composting_habit=True)

    w1 = calculate_waste_emissions(no_compost)
    w2 = calculate_waste_emissions(with_compost)

    assert w2 < w1
    assert pytest.approx(w2 / w1, rel=1e-2) == Config.COMPOSTING_DISCOUNT

def test_total_footprint_structure_and_benchmarks():
    """Verify total calculation converts kg to metric tonnes and includes breakdown."""
    sample = {
        "vehicle_miles_per_week": 150.0,
        "vehicle_mpg": 30.0,
        "vehicle_maintenance": True,
        "transit_miles_per_week": 20.0,
        "flights_per_year": 1.0,
        "electricity_kwh_per_month": 350.0,
        "clean_energy_pct": 0.0,
        "heating_units_per_month": 20.0,
        "waste_bags_per_week": 2.0,
        "recycling_habit": "regularly",
        "composting_habit": True,
        "diet_habit": "average",
        "shopping_habit": "average",
        "reusable_habit": True
    }
    result = calculate_total_footprint(sample)

    assert "total_kg" in result
    assert "total_tonnes" in result
    assert "breakdown" in result
    assert "benchmarks" in result
    assert "recommendations" in result

    # Tonnes should be kg / 1000
    assert pytest.approx(result["total_tonnes"], abs=0.01) == result["total_kg"] / 1000.0

    # Sum of percentages should be approximately 100%
    bk = result["breakdown"]
    total_pct = (
        bk["transportation"]["percentage"] +
        bk["energy"]["percentage"] +
        bk["waste"]["percentage"] +
        bk["other"]["percentage"]
    )
    assert pytest.approx(total_pct, abs=0.5) == 100.0

def test_recommendations_generation():
    """Ensure recommendations are tailored to high-emission metrics."""
    high_emissions = {
        "vehicle_miles_per_week": 350.0,
        "vehicle_mpg": 20.0,
        "vehicle_maintenance": False,
        "flights_per_year": 5.0,
        "electricity_kwh_per_month": 800.0,
        "clean_energy_pct": 0.0,
        "waste_bags_per_week": 4.0,
        "recycling_habit": "never",
        "composting_habit": False,
        "diet_habit": "meat_heavy"
    }
    calc = calculate_total_footprint(high_emissions)
    recs = calc["recommendations"]

    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert "transportation" in categories
