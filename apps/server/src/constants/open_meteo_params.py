"""
Open-Meteo API Parameter Mappings

This file defines:
1. Which parameters to request from each Open-Meteo endpoint
2. How Open-Meteo parameter names map to your database columns
3. Extraction frequencies (how often to update data)
4. Model information for the weather_models table
5. Parameter information for the weather_parameters table

Why this matters:
- Keeps API parameters centralized and maintainable
- Prevents typos in API requests
- Easy to add/remove parameters without changing code
- Single source of truth for data extraction
"""

# ==================== WEATHER FORECAST PARAMETERS ====================

"""
    Parameters for Open-Meteo forecast current endpoint
    These are the exact strings to send to the API
    
    Maps to: current_weather table
"""
WEATHER_CURRENT_PARAMS = {
    
    "api_params": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m",
    
    "db_mapping": {
        # Open-Meteo parameter → database column
        "temperature_2m": "temperature_2m",
        "relative_humidity_2m": "relative_humidity_2m",
        "apparent_temperature": "apparent_temperature",
        "precipitation": "precipitation",
        "weather_code": "weather_code",
        "cloud_cover": "cloud_cover",
        "wind_speed_10m": "wind_speed_10m",
        "wind_direction_10m": "wind_direction_10m",
    }
}
"""
    Parameters for Open-Meteo forecast hourly endpoint
    
    Maps to: weather_forecasts + forecast_data tables
"""
WEATHER_HOURLY_PARAMS = {
   
    "api_params": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
    
    "db_mapping": {
        "temperature_2m": "value",
        "relative_humidity_2m": "value",
        "precipitation_probability": "value",
        "precipitation": "value",
        "weather_code": "value",
        "wind_speed_10m": "value",
        "wind_direction_10m": "value",
    }
}

"""
    Parameters for Open-Meteo forecast daily endpoint
    
    Maps to: weather_forecasts_daily table
"""
WEATHER_DAILY_PARAMS = {
    "api_params": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours,precipitation_probability_max,weather_code,sunrise,sunset,sunshine_duration,uv_index_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant",
    
    "db_mapping": {
        "temperature_2m_max": "temperature_2m_max",
        "temperature_2m_min": "temperature_2m_min",
        "precipitation_sum": "precipitation_sum",
        "precipitation_hours": "precipitation_hours",
        "precipitation_probability_max": "precipitation_probability_max",
        "weather_code": "weather_code",
        "sunrise": "sunrise",
        "sunset": "sunset",
        "sunshine_duration": "sunshine_duration",
        "uv_index_max": "uv_index_max",
        "wind_speed_10m_max": "wind_speed_10m_max",
        "wind_gusts_10m_max": "wind_gusts_10m_max",
        "wind_direction_10m_dominant": "wind_direction_10m_dominant",
    }
}

# ==================== AIR QUALITY PARAMETERS ====================
"""
    Parameters for Open-Meteo air-quality current endpoint
    
    Maps to: air_quality_current table
"""
AIR_QUALITY_CURRENT_PARAMS = {
    "api_params": "pm2_5,pm10,european_aqi,us_aqi,nitrogen_dioxide,ozone,sulphur_dioxide,carbon_monoxide,dust,ammonia",
    
    "db_mapping": {
        "pm2_5": "pm2_5",
        "pm10": "pm10",
        "european_aqi": "european_aqi",
        "us_aqi": "us_aqi",
        "nitrogen_dioxide": "nitrogen_dioxide",
        "ozone": "ozone",
        "sulphur_dioxide": "sulphur_dioxide",
        "carbon_monoxide": "carbon_monoxide",
        "dust": "dust",
        "ammonia": "ammonia",
    }
}
"""
    Parameters for Open-Meteo air-quality hourly endpoint
    
    Maps to: air_quality_forecasts + air_quality_data tables
"""
AIR_QUALITY_HOURLY_PARAMS = {
    "api_params": "pm2_5,pm10,european_aqi,us_aqi,nitrogen_dioxide,ozone,sulphur_dioxide,carbon_monoxide",
    
    "db_mapping": {
        "pm2_5": "value",
        "pm10": "value",
        "european_aqi": "value",
        "us_aqi": "value",
        "nitrogen_dioxide": "value",
        "ozone": "value",
        "sulphur_dioxide": "value",
        "carbon_monoxide": "value",
    }
}

# ==================== MARINE PARAMETERS ====================

"""
    Parameters for Open-Meteo marine current endpoint
    
    Maps to: marine_current table
"""
MARINE_CURRENT_PARAMS = {
    "api_params": "wave_height,wave_direction,wave_period,swell_wave_height,swell_wave_direction,swell_wave_period,wind_wave_height,sea_surface_temperature,ocean_current_velocity,ocean_current_direction",
    
    "db_mapping": {
        "wave_height": "wave_height",
        "wave_direction": "wave_direction",
        "wave_period": "wave_period",
        "swell_wave_height": "swell_wave_height",
        "swell_wave_direction": "swell_wave_direction",
        "swell_wave_period": "swell_wave_period",
        "wind_wave_height": "wind_wave_height",
        "sea_surface_temperature": "sea_surface_temperature",
        "ocean_current_velocity": "ocean_current_velocity",
        "ocean_current_direction": "ocean_current_direction",
    }
}
"""
    Parameters for Open-Meteo marine hourly endpoint
    
    Maps to: marine_forecasts + marine_data tables
"""
MARINE_HOURLY_PARAMS = {
    "api_params": "wave_height,wave_direction,wave_period,swell_wave_height,swell_wave_direction,swell_wave_period,wind_wave_height,sea_surface_temperature",
    
    "db_mapping": {
        "wave_height": "value",
        "wave_direction": "value",
        "wave_period": "value",
        "swell_wave_height": "value",
        "swell_wave_direction": "value",
        "swell_wave_period": "value",
        "wind_wave_height": "value",
        "sea_surface_temperature": "value",
    }
}

"""
    Parameters for Open-Meteo marine daily endpoint
    
    Maps to: marine_forecasts_daily table
"""
MARINE_DAILY_PARAMS = {
    "api_params": "wave_height_max,wave_direction_dominant,wave_period_max,swell_wave_height_max,swell_wave_direction_dominant,wind_wave_height_max",
    
    "db_mapping": {
        "wave_height_max": "wave_height_max",
        "wave_direction_dominant": "wave_direction_dominant",
        "wave_period_max": "wave_period_max",
        "swell_wave_height_max": "swell_wave_height_max",
        "swell_wave_direction_dominant": "swell_wave_direction_dominant",
        "wind_wave_height_max": "wind_wave_height_max",
    }
}

# ==================== SATELLITE RADIATION PARAMETERS ====================

"""
    Parameters for Open-Meteo solar endpoint (also called 'solar' not 'satellite')
    
    Maps to: satellite_radiation_data table
    
    Note: This endpoint has 10-30 minute granularity (not hourly)
"""
SATELLITE_RADIATION_PARAMS = {
    "api_params": "shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance,terrestrial_radiation",
    
    "db_mapping": {
        "shortwave_radiation": "shortwave_radiation",
        "direct_radiation": "direct_radiation",
        "diffuse_radiation": "diffuse_radiation",
        "direct_normal_irradiance": "direct_normal_irradiance",
        "global_tilted_irradiance": "global_tilted_irradiance",
        "terrestrial_radiation": "terrestrial_radiation",
    },
    
    "panel_defaults": {
        "panel_tilt_angle": 0,        # Degrees from horizontal (0-90)
        "panel_azimuth_angle": 0,      # Degrees from north (0-360, 0=North, 90=East, 180=South, 270=West)
    }
}

# ==================== CLIMATE PROJECTIONS PARAMETERS ====================
"""
    Parameters for Open-Meteo climate?daily endpoint
    
    Maps to: climate_projections + climate_daily tables
    
    Note: Climate endpoint requires start_date and end_date parameters
"""
CLIMATE_DAILY_PARAMS = {
    "api_params": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,rain_sum,snowfall_sum,relative_humidity_2m_max,relative_humidity_2m_min,relative_humidity_2m_mean,wind_speed_10m_mean,wind_speed_10m_max,pressure_msl_mean,cloud_cover_mean,shortwave_radiation_sum,soil_moisture_0_to_10cm_mean",
    
    "db_mapping": {
        "temperature_2m_max": "temperature_2m_max",
        "temperature_2m_min": "temperature_2m_min",
        "temperature_2m_mean": "temperature_2m_mean",
        "precipitation_sum": "precipitation_sum",
        "rain_sum": "rain_sum",
        "snowfall_sum": "snowfall_sum",
        "relative_humidity_2m_max": "relative_humidity_2m_max",
        "relative_humidity_2m_min": "relative_humidity_2m_min",
        "relative_humidity_2m_mean": "relative_humidity_2m_mean",
        "wind_speed_10m_mean": "wind_speed_10m_mean",
        "wind_speed_10m_max": "wind_speed_10m_max",
        "pressure_msl_mean": "pressure_msl_mean",
        "cloud_cover_mean": "cloud_cover_mean",
        "shortwave_radiation_sum": "shortwave_radiation_sum",
        "soil_moisture_0_to_10cm_mean": "soil_moisture_0_to_10cm_mean",
    }
}

# ==================== DATA EXTRACTION FREQUENCIES ====================

"""
How often to extract each type of data
Values are in MINUTES

Explanation:
- 15 minutes: Update very frequently (current weather, real-time needs)
- 180 minutes (3 hours): Update regularly (forecast updates)
- 1440 minutes (24 hours): Update daily (daily forecasts)
- None: On-demand only (climate projections, which are historical/future)
"""

EXTRACTION_FREQUENCIES = {
    "current_weather": 15,           # Every 15 minutes
    "weather_hourly": 180,           # Every 3 hours
    "weather_daily": 1440,           # Every 24 hours (once per day)
    "air_quality_current": 15,       # Every 15 minutes
    "air_quality_hourly": 360,       # Every 6 hours
    "marine_current": 15,            # Every 15 minutes
    "marine_hourly": 720,            # Every 12 hours
    "marine_daily": 1440,            # Every 24 hours (once per day)
    "satellite_radiation": 1440,     # Every 24 hours (once per day)
    "climate_projections": None,     # On-demand only
}

# ==================== OPEN-METEO MODEL DEFINITIONS ====================

"""
This data will be inserted into the weather_models table
Based on ACTUAL Open-Meteo models and their specifications

Fields mapping to weather_models table:
- model_code: Unique identifier (short name)
- model_name: Human-readable name
- provider: Organization providing the model
- provider_country: Country where provider is based
- resolution_km: Spatial resolution in kilometers
- resolution_degrees: Spatial resolution in degrees
- forecast_days: Number of days forecasted
- update_frequency_hours: How often model updates
- temporal_resolution: Hourly, daily, etc.
- geographic_coverage: Global, regional, or local
- model_type: Type of weather data
- is_active: Whether we're actively using it
- description: Human-readable description
"""

WEATHER_MODELS_DATA = [
    {
        "model_code": "OM_FORECAST",
        "model_name": "Open-Meteo Forecast Model",
        "provider": "Open-Meteo",
        "provider_country": "Switzerland",
        "resolution_km": 11.0,
        "resolution_degrees": 0.1,
        "forecast_days": 16,
        "update_frequency_hours": 6,
        "temporal_resolution": "hourly",
        "geographic_coverage": "global",
        "model_type": "weather",
        "is_active": True,
        "description": "Open-Meteo weather forecast model with global coverage. Provides current, hourly, and daily forecasts.",
    },
    {
        "model_code": "CAMS_EUROPE",
        "model_name": "CAMS Europe Air Quality Model",
        "provider": "Copernicus",
        "provider_country": "European Union",
        "resolution_km": 10.0,
        "resolution_degrees": 0.1,
        "forecast_days": 5,
        "update_frequency_hours": 6,
        "temporal_resolution": "hourly",
        "geographic_coverage": "regional",
        "model_type": "air_quality",
        "is_active": True,
        "description": "CAMS Europe air quality forecasts. Covers Europe with high-resolution data for PM2.5, PM10, and pollutants.",
    },
    {
        "model_code": "ECMWF_WAVES",
        "model_name": "ECMWF Wave Model",
        "provider": "ECMWF",
        "provider_country": "European Union",
        "resolution_km": 28.0,
        "resolution_degrees": 0.25,
        "forecast_days": 10,
        "update_frequency_hours": 12,
        "temporal_resolution": "hourly",
        "geographic_coverage": "global",
        "model_type": "marine",
        "is_active": True,
        "description": "ECMWF wave and marine weather forecasts. Provides wave height, direction, period, and marine parameters.",
    },
    {
        "model_code": "CAMS_SOLAR",
        "model_name": "CAMS Solar Radiation",
        "provider": "Copernicus",
        "provider_country": "European Union",
        "resolution_km": 5.0,
        "resolution_degrees": 0.05,
        "forecast_days": 16,
        "update_frequency_hours": 3,
        "temporal_resolution": "15minutely",
        "geographic_coverage": "global",
        "model_type": "satellite_radiation",
        "is_active": True,
        "description": "CAMS Solar radiation data. High-resolution solar irradiance for solar energy applications (15-30 minute resolution).",
    },
    {
        "model_code": "EC_Earth3P_HR",
        "model_name": "EC_Earth3P-HR",
        "provider": "EC-Earth Consortium",
        "provider_country": "Europoean Union",
        "resolution_km": 29.0,
        "resolution_degrees": 0.261261,
        "forecast_days": 0,
        "update_frequency_hours": 0,
        "temporal_resolution": "daily",
        "geographic_coverage": "global",
        "model_type": "climate",
        "is_active": True,
        "description": "CMCC climate change projections. Long-term climate projections for future scenarios (historical and future data).",
    },
]

# ==================== WEATHER PARAMETER DEFINITIONS ====================

"""
This data will be inserted into the weather_parameters table
Defines all parameters available in the system

Fields:
- parameter_code: Short identifier
- parameter_name: Human-readable name
- unit: Unit of measurement
- parameter_category: Grouping (temperature, humidity, wind, etc.)
- data_type: SQL data type (float, int, varchar)
- altitude_level: Height above ground where measured
- is_surface: Is this surface data (True) or upper atmosphere (False)
- api_endpoint: Which Open-Meteo endpoint provides this
"""

WEATHER_PARAMETERS_DATA = [
    # Weather Temperature Parameters
    ("temp_2m", "Temperature 2m", "°C", "temperature", "float", "2m", True, "forecast"),
    ("temp_2m_max", "Temperature Max 2m", "°C", "temperature", "float", "2m", True, "forecast"),
    ("temp_2m_min", "Temperature Min 2m", "°C", "temperature", "float", "2m", True, "forecast"),
    ("temp_2m_mean", "Temperature Mean 2m", "°C", "temperature", "float", "2m", True, "forecast"),
    ("apparent_temp", "Apparent Temperature", "°C", "temperature", "float", "2m", True, "forecast"),
    
    # Weather Humidity Parameters
    ("humidity_2m", "Relative Humidity 2m", "%", "humidity", "int", "2m", True, "forecast"),
    ("humidity_2m_max", "Humidity Max", "%", "humidity", "int", "2m", True, "forecast"),
    ("humidity_2m_min", "Humidity Min", "%", "humidity", "int", "2m", True, "forecast"),
    ("humidity_2m_mean", "Humidity Mean", "%", "humidity", "int", "2m", True, "forecast"),
    
    # Weather Precipitation Parameters
    ("precip", "Precipitation", "mm", "precipitation", "float", "surface", True, "forecast"),
    ("precip_sum", "Precipitation Sum", "mm", "precipitation", "float", "surface", True, "forecast"),
    ("precip_prob", "Precipitation Probability", "%", "precipitation", "int", "surface", True, "forecast"),
    ("precip_prob_max", "Precipitation Probability Max", "%", "precipitation", "int", "surface", True, "forecast"),
    ("precip_hours", "Precipitation Hours", "hours", "precipitation", "int", "surface", True, "forecast"),
    
    # Weather Wind Parameters
    ("wind_speed_10m", "Wind Speed 10m", "km/h", "wind", "float", "10m", True, "forecast"),
    ("wind_speed_10m_max", "Wind Speed Max 10m", "km/h", "wind", "float", "10m", True, "forecast"),
    ("wind_speed_10m_mean", "Wind Speed Mean 10m", "km/h", "wind", "float", "10m", True, "forecast"),
    ("wind_dir_10m", "Wind Direction 10m", "°", "wind", "int", "10m", True, "forecast"),
    ("wind_dir_10m_dominant", "Wind Direction Dominant", "°", "wind", "int", "10m", True, "forecast"),
    ("wind_gusts_10m_max", "Wind Gusts Max 10m", "km/h", "wind", "float", "10m", True, "forecast"),
    
    # Weather Cloud & Solar Parameters
    ("cloud_cover", "Cloud Cover", "%", "clouds", "int", "total", True, "forecast"),
    ("cloud_cover_mean", "Cloud Cover Mean", "%", "clouds", "float", "total", True, "forecast"),
    ("sunshine_duration", "Sunshine Duration", "seconds", "solar", "int", "surface", True, "forecast"),
    ("uv_index_max", "UV Index Max", "index", "solar", "float", "surface", True, "forecast"),
    
    # Weather Code Parameter
    ("weather_code", "Weather Code (WMO)", "code", "weather", "int", "surface", True, "forecast"),
    
    # Air Quality Parameters
    ("pm2_5", "PM2.5", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    ("pm10", "PM10", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    ("aqi_european", "European AQI", "index", "air_quality", "int", "surface", True, "air_quality"),
    ("aqi_us", "US AQI", "index", "air_quality", "int", "surface", True, "air_quality"),
    ("no2", "Nitrogen Dioxide (NO2)", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    ("o3", "Ozone (O3)", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    ("so2", "Sulphur Dioxide (SO2)", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    ("co", "Carbon Monoxide (CO)", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    ("dust", "Dust", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    ("nh3", "Ammonia (NH3)", "µg/m³", "air_quality", "float", "surface", True, "air_quality"),
    
    # Marine Parameters
    ("wave_height", "Wave Height", "m", "marine", "float", "surface", True, "marine"),
    ("wave_height_max", "Wave Height Max", "m", "marine", "float", "surface", True, "marine"),
    ("wave_direction", "Wave Direction", "°", "marine", "int", "surface", True, "marine"),
    ("wave_direction_dominant", "Wave Direction Dominant", "°", "marine", "int", "surface", True, "marine"),
    ("wave_period", "Wave Period", "s", "marine", "float", "surface", True, "marine"),
    ("wave_period_max", "Wave Period Max", "s", "marine", "float", "surface", True, "marine"),
    ("swell_wave_height", "Swell Wave Height", "m", "marine", "float", "surface", True, "marine"),
    ("swell_wave_height_max", "Swell Wave Height Max", "m", "marine", "float", "surface", True, "marine"),
    ("swell_wave_direction", "Swell Wave Direction", "°", "marine", "int", "surface", True, "marine"),
    ("swell_wave_direction_dominant", "Swell Direction Dominant", "°", "marine", "int", "surface", True, "marine"),
    ("swell_wave_period", "Swell Wave Period", "s", "marine", "float", "surface", True, "marine"),
    ("swell_wave_period_max", "Swell Period Max", "s", "marine", "float", "surface", True, "marine"),
    ("wind_wave_height", "Wind Wave Height", "m", "marine", "float", "surface", True, "marine"),
    ("sea_temp", "Sea Surface Temperature", "°C", "marine", "float", "surface", True, "marine"),
    ("sea_temp_mean", "Sea Temperature Mean", "°C", "marine", "float", "surface", True, "marine"),
    ("ocean_current_vel", "Ocean Current Velocity", "m/s", "marine", "float", "surface", True, "marine"),
    ("ocean_current_vel_max", "Ocean Current Velocity Max", "m/s", "marine", "float", "surface", True, "marine"),
    ("ocean_current_dir", "Ocean Current Direction", "°", "marine", "int", "surface", True, "marine"),
    
    # Satellite Radiation Parameters
    ("shortwave_rad", "Shortwave Radiation", "W/m²", "solar", "float", "surface", True, "satellite_radiation"),
    ("direct_rad", "Direct Radiation", "W/m²", "solar", "float", "surface", True, "satellite_radiation"),
    ("diffuse_rad", "Diffuse Radiation", "W/m²", "solar", "float", "surface", True, "satellite_radiation"),
    ("dni", "Direct Normal Irradiance (DNI)", "W/m²", "solar", "float", "surface", True, "satellite_radiation"),
    ("gti", "Global Tilted Irradiance (GTI)", "W/m²", "solar", "float", "surface", True, "satellite_radiation"),
    ("terrestrial_rad", "Terrestrial Radiation", "W/m²", "solar", "float", "surface", True, "satellite_radiation"),
    
    # Climate Parameters
    ("precip_rain_sum", "Rain Sum", "mm", "precipitation", "float", "surface", True, "climate"),
    ("precip_snow_sum", "Snowfall Sum", "mm", "precipitation", "float", "surface", True, "climate"),
    ("pressure_msl_mean", "Pressure Mean MSL", "hPa", "pressure", "float", "surface", True, "climate"),
    ("radiation_shortwave_sum", "Shortwave Radiation Sum", "MJ/m²", "solar", "float", "surface", True, "climate"),
    ("soil_moisture_0_10cm", "Soil Moisture 0-10cm", "m³/m³", "soil", "float", "0-10cm", False, "climate"),
]

# ==================== HELPER FUNCTIONS ====================

def get_api_params(endpoint_type: str, data_type: str) -> dict:
    """
    Get API parameters for a specific endpoint
    
    Args:
        endpoint_type: Type of endpoint ('weather', 'air_quality', 'marine', 'satellite', 'climate')
        data_type: Data type ('current', 'hourly', 'daily')
    
    Returns:
        Dictionary with 'api_params' and 'db_mapping'
    
    Example:
        params = get_api_params('weather', 'current')
        # Returns: {"api_params": "temperature_2m,humidity_2m,...", "db_mapping": {...}}
    """
    
    params_map = {
        ("weather", "current"): WEATHER_CURRENT_PARAMS,
        ("weather", "hourly"): WEATHER_HOURLY_PARAMS,
        ("weather", "daily"): WEATHER_DAILY_PARAMS,
        ("air_quality", "current"): AIR_QUALITY_CURRENT_PARAMS,
        ("air_quality", "hourly"): AIR_QUALITY_HOURLY_PARAMS,
        ("marine", "current"): MARINE_CURRENT_PARAMS,
        ("marine", "hourly"): MARINE_HOURLY_PARAMS,
        ("marine", "daily"): MARINE_DAILY_PARAMS,
        ("satellite", "hourly"): SATELLITE_RADIATION_PARAMS,
        ("climate", "daily"): CLIMATE_DAILY_PARAMS,
    }
    
    key = (endpoint_type, data_type)
    if key not in params_map:
        raise ValueError(f"Unknown endpoint: {endpoint_type}/{data_type}")
    
    return params_map[key]


def get_extraction_frequency(data_type: str) -> int:
    """
    Get extraction frequency for a data type
    
    Args:
        data_type: Key from EXTRACTION_FREQUENCIES dict
    
    Returns:
        Minutes between extractions, or None for on-demand
    
    Example:
        freq = get_extraction_frequency('current_weather')
        # Returns: 15 (every 15 minutes)
    """
    return EXTRACTION_FREQUENCIES.get(data_type)