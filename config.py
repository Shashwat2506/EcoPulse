"""
EcoPulse Configuration Module
Defines application settings and scientific illustrative emission factors.
All emission factors are based on documented EPA and DEFRA benchmark data.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "ecopulse-dev-secret-key-2026-sustainability")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    TESTING = False
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "ecopulse.db"))
    
    # Illustrative Emission Factors (Documented averages)
    # 1. Transportation
    # EPA: ~8.887 kg CO2 per gallon of gasoline
    EMISSION_FACTOR_GASOLINE_KG_PER_GALLON = 8.887
    # Default fuel economy (miles per gallon) if unprovided or 0
    DEFAULT_MPG = 25.0
    # Regular vehicle maintenance efficiency saving (~4% improvement)
    VEHICLE_MAINTENANCE_FACTOR = 0.96
    # Public transit: ~0.14 kg CO2e per passenger-mile (bus/subway weighted avg)
    EMISSION_FACTOR_TRANSIT_KG_PER_MILE = 0.14
    # Commercial aviation: ~450 kg CO2e per average individual flight
    EMISSION_FACTOR_FLIGHT_KG_PER_TRIP = 450.0

    # 2. Home Energy
    # Grid electricity: ~0.385 kg CO2e per kWh (US/Global grid mix average)
    EMISSION_FACTOR_ELECTRICITY_KG_PER_KWH = 0.385
    # Natural gas / home heating: ~5.3 kg CO2e per therm (or ~0.18 kg per kWh equiv)
    EMISSION_FACTOR_HEATING_KG_PER_UNIT = 5.3

    # 3. Waste
    # Average baseline waste emission: ~0.50 kg CO2e per kg landfill waste
    # Base municipal waste: ~1.8 kg/day per person (~650 kg/year baseline = ~325 kg CO2e)
    BASELINE_ANNUAL_WASTE_KG_CO2 = 325.0
    # Recycling discount multipliers
    RECYCLING_DISCOUNT = {
        "never": 1.0,
        "sometimes": 0.85,
        "regularly": 0.70,
        "strictly": 0.55,
    }
    # Composting discount multiplier
    COMPOSTING_DISCOUNT = 0.80  # 20% methane diversion reduction

    # 4. Other Lifestyle Factors (Diet & Consumption)
    DIET_ANNUAL_KG_CO2 = {
        "meat_heavy": 2500.0,
        "average": 1900.0,
        "pescatarian": 1400.0,
        "vegetarian": 1200.0,
        "vegan": 900.0,
    }
    CONSUMPTION_ANNUAL_KG_CO2 = {
        "minimalist": 400.0,
        "average": 800.0,
        "frequent_shopper": 1400.0,
    }
    REUSABLE_HABITS_DISCOUNT = 0.92  # 8% reduction for consistent reusables

    # Illustrative Comparative Benchmarks (in Metric Tonnes CO2e/year)
    BENCHMARK_GLOBAL_AVG = 4.0
    BENCHMARK_US_AVG = 16.0
    BENCHMARK_EU_AVG = 7.0
    BENCHMARK_PARIS_TARGET = 2.0


class TestConfig(Config):
    """Test configuration using an in-memory database or temp path."""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = ":memory:"
