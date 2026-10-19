"""
EcoPulse Carbon Calculation Engine
Transparent, modular, and scientifically documented calculations for personal carbon footprint.

Units:
- Inputs are collected in conventional consumer units (miles/week, kWh/month, etc.).
- Calculations determine mass in kilograms of CO2-equivalent (kg CO2e).
- Results are converted to metric tonnes (1 metric tonne = 1,000 kg).
"""

from typing import Dict, Any, Tuple, List
from config import Config

def validate_metric_input(raw_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """
    Validates form data ensuring numbers are non-negative and well-formed.
    Returns: (is_valid, errors_dict, cleaned_data)
    """
    errors: Dict[str, str] = {}
    cleaned: Dict[str, Any] = {}

    # Numeric fields with non-negative constraints
    numeric_fields = {
        "vehicle_miles_per_week": (0.0, 5000.0, "Miles per week must be between 0 and 5000."),
        "vehicle_mpg": (1.0, 150.0, "Fuel economy must be between 1 and 150 mpg."),
        "transit_miles_per_week": (0.0, 5000.0, "Transit miles per week must be between 0 and 5000."),
        "flights_per_year": (0.0, 200.0, "Flights per year must be between 0 and 200."),
        "electricity_kwh_per_month": (0.0, 20000.0, "Electricity usage must be between 0 and 20,000 kWh/month."),
        "heating_units_per_month": (0.0, 1000.0, "Heating energy must be between 0 and 1,000 units/month."),
        "waste_bags_per_week": (0.0, 50.0, "Waste bags per week must be between 0 and 50.")
    }

    # Default fallbacks
    defaults = {
        "vehicle_miles_per_week": 200.0,
        "vehicle_mpg": 30.0,
        "vehicle_maintenance": True,
        "transit_miles_per_week": 50.0,
        "flights_per_year": 2.0,
        "electricity_kwh_per_month": 450.0,
        "clean_energy_pct": 0.0,
        "heating_units_per_month": 30.0,
        "waste_bags_per_week": 2.0,
        "recycling_habit": "regularly",
        "composting_habit": False,
        "diet_habit": "average",
        "shopping_habit": "average",
        "reusable_habit": True
    }

    for field, (min_val, max_val, err_msg) in numeric_fields.items():
        val = raw_data.get(field)
        if val is None or val == "":
            cleaned[field] = defaults[field]
            continue
        try:
            num = float(val)
            if num < min_val or num > max_val:
                errors[field] = err_msg
            else:
                cleaned[field] = num
        except (ValueError, TypeError):
            errors[field] = f"Invalid number for {field.replace('_', ' ')}."

    # Clean energy percentage
    clean_val = raw_data.get("clean_energy_pct", 0.0)
    try:
        clean_num = float(clean_val) if clean_val not in (None, "") else 0.0
        if 0.0 <= clean_num <= 100.0:
            cleaned["clean_energy_pct"] = clean_num
        else:
            errors["clean_energy_pct"] = "Clean energy percentage must be between 0 and 100%."
    except (ValueError, TypeError):
        errors["clean_energy_pct"] = "Invalid clean energy percentage."

    # Boolean checkboxes
    def parse_bool(val: Any) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "on", "yes")
        if isinstance(val, (int, float)):
            return bool(val)
        return False

    cleaned["vehicle_maintenance"] = parse_bool(raw_data.get("vehicle_maintenance", defaults["vehicle_maintenance"]))
    cleaned["composting_habit"] = parse_bool(raw_data.get("composting_habit", defaults["composting_habit"]))
    cleaned["reusable_habit"] = parse_bool(raw_data.get("reusable_habit", defaults["reusable_habit"]))

    # Categorical strings
    recycling = str(raw_data.get("recycling_habit", defaults["recycling_habit"])).lower()
    if recycling not in Config.RECYCLING_DISCOUNT:
        recycling = defaults["recycling_habit"]
    cleaned["recycling_habit"] = recycling

    diet = str(raw_data.get("diet_habit", defaults["diet_habit"])).lower()
    if diet not in Config.DIET_ANNUAL_KG_CO2:
        diet = defaults["diet_habit"]
    cleaned["diet_habit"] = diet

    shopping = str(raw_data.get("shopping_habit", defaults["shopping_habit"])).lower()
    if shopping not in Config.CONSUMPTION_ANNUAL_KG_CO2:
        shopping = defaults["shopping_habit"]
    cleaned["shopping_habit"] = shopping

    is_valid = len(errors) == 0
    return is_valid, errors, cleaned


def calculate_transportation_emissions(data: Dict[str, Any], cfg: Config = Config) -> float:
    """
    Calculates annual transportation emissions in kg CO2e.
    Personal vehicle: (miles/week / mpg) * 52 weeks * 8.887 kg/gal * maintenance_factor
    Transit: miles/week * 52 weeks * 0.14 kg/mile
    Aviation: flights/year * 450 kg/flight
    """
    miles_per_week = data.get("vehicle_miles_per_week", 0.0)
    mpg = data.get("vehicle_mpg", cfg.DEFAULT_MPG)
    if mpg <= 0:
        mpg = cfg.DEFAULT_MPG

    # Personal vehicle
    weekly_gallons = miles_per_week / mpg
    annual_gallons = weekly_gallons * 52.0
    gasoline_emissions = annual_gallons * cfg.EMISSION_FACTOR_GASOLINE_KG_PER_GALLON

    if data.get("vehicle_maintenance", False):
        gasoline_emissions *= cfg.VEHICLE_MAINTENANCE_FACTOR

    # Public transit
    transit_miles = data.get("transit_miles_per_week", 0.0)
    transit_emissions = transit_miles * 52.0 * cfg.EMISSION_FACTOR_TRANSIT_KG_PER_MILE

    # Aviation
    flights = data.get("flights_per_year", 0.0)
    flight_emissions = flights * cfg.EMISSION_FACTOR_FLIGHT_KG_PER_TRIP

    return round(gasoline_emissions + transit_emissions + flight_emissions, 2)


def calculate_home_energy_emissions(data: Dict[str, Any], cfg: Config = Config) -> float:
    """
    Calculates annual home energy emissions in kg CO2e.
    Electricity: (kWh/month * 12) * 0.385 kg/kWh * (1 - clean_energy_pct / 100)
    Heating: (heating_units/month * 12) * 5.3 kg/unit
    """
    kwh_per_month = data.get("electricity_kwh_per_month", 0.0)
    annual_kwh = kwh_per_month * 12.0
    clean_pct = min(max(data.get("clean_energy_pct", 0.0), 0.0), 100.0)
    grid_share = (100.0 - clean_pct) / 100.0

    electricity_emissions = annual_kwh * cfg.EMISSION_FACTOR_ELECTRICITY_KG_PER_KWH * grid_share

    heating_units = data.get("heating_units_per_month", 0.0)
    annual_heating = heating_units * 12.0
    heating_emissions = annual_heating * cfg.EMISSION_FACTOR_HEATING_KG_PER_UNIT

    return round(electricity_emissions + heating_emissions, 2)


def calculate_waste_emissions(data: Dict[str, Any], cfg: Config = Config) -> float:
    """
    Calculates annual waste emissions in kg CO2e.
    Baseline waste scaled by weekly bag count relative to standard 2 bags/week.
    Discounts applied for recycling and composting.
    """
    bags_per_week = data.get("waste_bags_per_week", 2.0)
    bag_ratio = max(bags_per_week / 2.0, 0.1)
    base_emissions = cfg.BASELINE_ANNUAL_WASTE_KG_CO2 * bag_ratio

    recycling_habit = data.get("recycling_habit", "regularly")
    recycling_factor = cfg.RECYCLING_DISCOUNT.get(recycling_habit, 0.85)

    waste_emissions = base_emissions * recycling_factor

    if data.get("composting_habit", False):
        waste_emissions *= cfg.COMPOSTING_DISCOUNT

    return round(waste_emissions, 2)


def calculate_other_emissions(data: Dict[str, Any], cfg: Config = Config) -> float:
    """
    Calculates annual other lifestyle emissions in kg CO2e.
    Diet + Consumer shopping habits with reduction for reusable practices.
    """
    diet_habit = data.get("diet_habit", "average")
    diet_emissions = cfg.DIET_ANNUAL_KG_CO2.get(diet_habit, 1900.0)

    shopping_habit = data.get("shopping_habit", "average")
    shopping_emissions = cfg.CONSUMPTION_ANNUAL_KG_CO2.get(shopping_habit, 800.0)

    total_other = diet_emissions + shopping_emissions

    if data.get("reusable_habit", False):
        total_other *= cfg.REUSABLE_HABITS_DISCOUNT

    return round(total_other, 2)


def calculate_total_footprint(data: Dict[str, Any], cfg: Config = Config) -> Dict[str, Any]:
    """
    Comprehensive assessment calculation returning values in kg CO2e and Metric Tonnes CO2e.
    Also provides breakdown percentages, secondary metrics, and benchmark comparisons.
    """
    # Validate and clean inputs
    _, _, cleaned = validate_metric_input(data)

    transport_kg = calculate_transportation_emissions(cleaned, cfg)
    energy_kg = calculate_home_energy_emissions(cleaned, cfg)
    waste_kg = calculate_waste_emissions(cleaned, cfg)
    other_kg = calculate_other_emissions(cleaned, cfg)

    total_kg = transport_kg + energy_kg + waste_kg + other_kg
    total_tonnes = total_kg / 1000.0

    transport_tonnes = transport_kg / 1000.0
    energy_tonnes = energy_kg / 1000.0
    waste_tonnes = waste_kg / 1000.0
    other_tonnes = other_kg / 1000.0

    # Calculate category percentages
    if total_kg > 0:
        transport_pct = round((transport_kg / total_kg) * 100.0, 1)
        energy_pct = round((energy_kg / total_kg) * 100.0, 1)
        waste_pct = round((waste_kg / total_kg) * 100.0, 1)
        other_pct = round((other_kg / total_kg) * 100.0, 1)
    else:
        transport_pct = energy_pct = waste_pct = other_pct = 25.0

    # Secondary periodic metrics
    weekly_tonnes = total_tonnes / 52.0
    monthly_tonnes = total_tonnes / 12.0
    weekly_kg = total_kg / 52.0
    monthly_kg = total_kg / 12.0

    # Benchmark comparisons
    vs_global_pct = round(((total_tonnes - cfg.BENCHMARK_GLOBAL_AVG) / cfg.BENCHMARK_GLOBAL_AVG) * 100.0, 1)
    vs_us_pct = round(((total_tonnes - cfg.BENCHMARK_US_AVG) / cfg.BENCHMARK_US_AVG) * 100.0, 1)

    results = {
        "total_kg": round(total_kg, 2),
        "total_tonnes": round(total_tonnes, 2),
        "primary_display_tonnes": f"{total_tonnes:.1f}",
        "weekly_tonnes": round(weekly_tonnes, 3),
        "monthly_tonnes": round(monthly_tonnes, 2),
        "weekly_kg": round(weekly_kg, 1),
        "monthly_kg": round(monthly_kg, 1),
        "breakdown": {
            "transportation": {
                "kg": round(transport_kg, 1),
                "tonnes": round(transport_tonnes, 2),
                "percentage": transport_pct,
                "label": "Transportation"
            },
            "energy": {
                "kg": round(energy_kg, 1),
                "tonnes": round(energy_tonnes, 2),
                "percentage": energy_pct,
                "label": "Home Energy"
            },
            "waste": {
                "kg": round(waste_kg, 1),
                "tonnes": round(waste_tonnes, 2),
                "percentage": waste_pct,
                "label": "Waste"
            },
            "other": {
                "kg": round(other_kg, 1),
                "tonnes": round(other_tonnes, 2),
                "percentage": other_pct,
                "label": "Other Activities"
            }
        },
        "benchmarks": {
            "global_average": cfg.BENCHMARK_GLOBAL_AVG,
            "us_average": cfg.BENCHMARK_US_AVG,
            "eu_average": cfg.BENCHMARK_EU_AVG,
            "paris_target": cfg.BENCHMARK_PARIS_TARGET,
            "vs_global_diff_pct": vs_global_pct,
            "vs_us_diff_pct": vs_us_pct
        },
        "inputs": cleaned
    }

    results["recommendations"] = generate_recommendations(cleaned, results)
    return results


def generate_recommendations(inputs: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transparent, heuristic recommendation engine that yields high-impact, practical suggestions.
    Does not claim or use black-box machine learning.
    """
    recs = []

    # 1. Transportation Recommendations
    miles = inputs.get("vehicle_miles_per_week", 0.0)
    mpg = inputs.get("vehicle_mpg", 30.0)
    if miles > 120:
        est_savings_t = round(((miles * 0.20) / max(mpg, 15.0)) * 52.0 * 8.887 / 1000.0, 2)
        recs.append({
            "category": "transportation",
            "icon": "car",
            "badge": "High Impact",
            "title": "Optimize Commuting Habits",
            "description": f"Carpooling or replacing 20% of your personal vehicle miles with transit/cycling could save ~{est_savings_t} tonnes of CO2e annually."
        })

    if not inputs.get("vehicle_maintenance", True):
        recs.append({
            "category": "transportation",
            "icon": "wrench",
            "badge": "Quick Win",
            "title": "Routine Vehicle Maintenance",
            "description": "Keeping tires properly inflated and servicing filters improves fuel economy by ~4%, saving fuel cost and reducing tailpipe emissions."
        })

    flights = inputs.get("flights_per_year", 0.0)
    if flights >= 3:
        saved_flight_t = round(Config.EMISSION_FACTOR_FLIGHT_KG_PER_TRIP / 1000.0, 2)
        recs.append({
            "category": "transportation",
            "icon": "plane",
            "badge": "High Impact",
            "title": "Regional Rail Alternatives",
            "description": f"Swapping just one medium-haul flight for high-speed rail or direct travel saves roughly ~{saved_flight_t} tonnes of CO2e."
        })

    # 2. Home Energy Recommendations
    kwh = inputs.get("electricity_kwh_per_month", 0.0)
    clean_pct = inputs.get("clean_energy_pct", 0.0)
    if clean_pct < 50.0 and kwh > 300:
        clean_savings_t = round((kwh * 12.0 * 0.385 * 0.5) / 1000.0, 2)
        recs.append({
            "category": "energy",
            "icon": "bolt",
            "badge": "High Impact",
            "title": "Transition to Green Energy",
            "description": f"Enrolling in your utility provider's renewable energy tariff (wind/solar) could lower your footprint by up to {clean_savings_t} tonnes/year."
        })

    if kwh > 500:
        recs.append({
            "category": "energy",
            "icon": "leaf",
            "badge": "Actionable",
            "title": "Smart Thermostat & Vampire Power",
            "description": "Smart thermostats and power strips for home electronics can trim household energy use by 8-12% without sacrificing comfort."
        })

    # 3. Waste Recommendations
    recycling = inputs.get("recycling_habit", "regularly")
    if recycling in ("never", "sometimes"):
        recs.append({
            "category": "waste",
            "icon": "trash",
            "badge": "Quick Win",
            "title": "Standardize Household Recycling",
            "description": "Establishing consistent paper, aluminum, and rigid plastic recycling curbs landfill emissions by up to 30%."
        })

    if not inputs.get("composting_habit", False):
        recs.append({
            "category": "waste",
            "icon": "recycle",
            "badge": "Medium Impact",
            "title": "Compost Organic Food Scraps",
            "description": "Composting diverts food scraps from anaerobic landfills, stopping methane gas emissions before they form."
        })

    # 4. Other Lifestyle Recommendations
    diet = inputs.get("diet_habit", "average")
    if diet in ("meat_heavy", "average"):
        recs.append({
            "category": "other",
            "icon": "utensils",
            "badge": "Medium Impact",
            "title": "Plant-Forward Meal Swaps",
            "description": "Adopting Meatless Mondays or plant-based lunches two days a week can reduce personal emissions by over 0.4 tonnes annually."
        })

    # Default fallback recommendation if user already has an ultra-low footprint
    if not recs:
        recs.append({
            "category": "other",
            "icon": "award",
            "badge": "Exemplary",
            "title": "Maintain Sustainable Leadership",
            "description": "Your current habits produce significantly below-average emissions. Share your conservation strategies with peers and community groups!"
        })

    return recs[:4]  # Return top 4 most relevant recommendations
