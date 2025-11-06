"""
Database Initialization Script

Run this ONCE after creating the database schema to:
1. Populate weather_models table
2. Populate weather_parameters table
3. Populate model_parameters table
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from src.constants.open_meteo_params import WEATHER_MODELS_DATA, WEATHER_PARAMETERS_DATA
from src.db.database import DatabaseConnection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    
    db = DatabaseConnection()
    db.connect()
    db._owns_db = True
    
    """Initialize database with models and parameters"""
    
    print("\n" + "="*60)
    print("DATABASE INITIALIZATION")
    print("="*60 + "\n")

    
    try:
        
        query_parameters = """
        SELECT COUNT(*) FROM weather_parameters
        """
        
        query_models = """
        SELECT COUNT(*) FROM weather_models
        """
        
        query_models_p = """
        SELECT COUNT(*) FROM model_parameters
        """
        exist_weather_parameters = db.execute_query(query_parameters)[0][0]
        exist_weather_models = db.execute_query(query_models)[0][0]
        exist_model_parameters = db.execute_query(query_models_p)[0][0]
        
        if exist_weather_models == 0:
            # Initialize weather models
            print("Initializing weather models...")
            if initialize_weather_models(db):
                print("✓ Weather models initialized\n")
            else:
                print("✗ Failed to initialize weather models\n")
        else:
            print(f"Weather models table already has {exist_weather_parameters}")
            
        
        if exist_weather_parameters == 0:
            # Initialize weather parameters
            print("Initializing weather parameters...")
            if initialize_weather_parameters(db):
                print("✓ Weather parameters initialized\n")
            else:
                print("✗ Failed to initialize weather parameters\n")
        else:
            print(f"Weather Parameters table already has {exist_weather_parameters}")
        
        if exist_model_parameters == 0 :        
            # Initialize model_parameters
            if initialize_model_parameters(db):
                print("✓ Models parameters initialized\n")
            else:
                print("✗ Failed to initialize weather parameters\n")
        else:
            print("models parameters table already has {exist_model_parameters}")
        
        print("="*60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*60)
    
    finally:
       db.disconnect()
        

def initialize_weather_models(db) -> bool:
        """
        Initialize weather_models table with Open-Meteo models
            
        This should be run ONCE when setting up the database.
        Inserts all models from WEATHER_MODELS_DATA constant.
            
        Returns:
            True if successful
            
        Explanation:
        - Populates weather_models table
        - Uses INSERT IGNORE to avoid duplicates
        - Should be called during database setup
        """
            
        query = """
        INSERT IGNORE INTO weather_models (
            model_code, model_name, provider, provider_country,
            resolution_km, resolution_degrees, forecast_days,
            update_frequency_hours, temporal_resolution,
            geographic_coverage, model_type, is_active,
            description, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
            """
            
        rows = []
        for model in WEATHER_MODELS_DATA:
            row = (
                model['model_code'],
                model['model_name'],
                model['provider'],
                model['provider_country'],
                model['resolution_km'],
                model['resolution_degrees'],
                model['forecast_days'],
                model['update_frequency_hours'],
                model['temporal_resolution'],
                model['geographic_coverage'],
                model['model_type'],
                model['is_active'],
                model['description'],
            )
            rows.append(row)
            
        try:
            rows_inserted = db.execute_bulk_insert(query, rows)
            logger.info(f"✓ Initialized {rows_inserted} weather models")
            return True
        except Exception as e:
            logger.error(f"Database error in initialize weather_models_data: {e}")
            return False

def initialize_weather_parameters(db) -> bool:
        """
        Initialize weather_parameters table with all parameters
        
        This should be run ONCE when setting up the database.
        Inserts all parameters from WEATHER_PARAMETERS_DATA constant.
        
        Returns:
            True if successful
        
        Explanation:
        - Populates weather_parameters table
        - Uses INSERT IGNORE to avoid duplicates
        - Should be called during database setup
        """
    
        
        query = """
        INSERT IGNORE INTO weather_parameters (
            parameter_code, parameter_name, description, unit, parameter_category,
            data_type, altitude_level, is_surface, api_endpoint,
            created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        """
        rows = []
        for model in WEATHER_PARAMETERS_DATA:
            row = (
                model[0],
                model[1],
                None,
                model[2],
                model[3],
                model[4],
                model[5],
                model[6],
                model[7],
            )
            rows.append(row)
    
        try:
            rows_inserted = db.execute_bulk_insert(query, rows)
            logger.info(f"✓ Initialized {rows_inserted} weather parameters")
            return True
        except Exception as e:
            logger.error(f"Database error in initialize weather_parameters: {e}")
            return False

def initialize_model_parameters(db) -> bool:
    """
    Initialize model_parameters table by linking models to their supported parameters
    
    This creates the many-to-many relationship between:
    - weather_models (which models exist)
    - weather_parameters (which parameters each model supports)
    
    Based on Open-Meteo API documentation and our open_meteo_params.py definitions.
    
    Returns:
        True if successful
    
    How it works:
    1. Get all model IDs and parameter IDs from database
    2. Define which parameters each model supports
    3. Insert the relationships with appropriate data_quality ratings
    """
    
    try:
        # Get all model IDs
        models_query = "SELECT model_id, model_code FROM weather_models"
        models = db.execute_query(models_query)
        model_map = {code: model_id for model_id, code in models}
        
        # Get all parameter IDs
        params_query = "SELECT parameter_id, parameter_code FROM weather_parameters"
        params = db.execute_query(params_query)
        param_map = {code: param_id for param_id, code in params}
        
        logger.info(f"Found {len(model_map)} models and {len(param_map)} parameters")
        
        # Define model-parameter relationships
        model_parameters_mapping = get_model_parameters_mapping()
        
        # Build insert rows
        # CORRECTED: Using data_quality column instead of temporal_resolution
        insert_query = """
        INSERT IGNORE INTO model_parameters (
            model_id, parameter_id, is_available, 
            data_quality, added_at
        ) VALUES (%s, %s, %s, %s, NOW())
        """
        
        rows = []
        total_mappings = 0
        
        for model_code, param_definitions in model_parameters_mapping.items():
            if model_code not in model_map:
                logger.warning(f"Model {model_code} not found in database")
                continue
            
            model_id = model_map[model_code]
            
            # param_definitions now contains (param_code, data_quality)
            for param_code, data_quality in param_definitions:
                if param_code not in param_map:
                    logger.warning(f"Parameter {param_code} not found in database")
                    continue
                
                param_id = param_map[param_code]
                
                row = (
                    model_id,
                    param_id,
                    True,  # is_available
                    data_quality,  # Using data_quality ('high', 'medium', 'low', 'interpolated')
                )
                rows.append(row)
                total_mappings += 1
        
        # Bulk insert
        if rows:
            rows_inserted = db.execute_bulk_insert(insert_query, rows)
            logger.info(f"✓ Initialized {rows_inserted} model-parameter relationships")
            
            # Show summary by model
            print("\nModel-Parameter Summary:")
            print("-" * 60)
            for model_code, model_id in model_map.items():
                count_query = """
                SELECT COUNT(*) FROM model_parameters 
                WHERE model_id = %s
                """
                count = db.execute_query(count_query, (model_id,))[0][0]
                print(f"  {model_code:20} - {count:3} parameters")
            print("-" * 60)
            
            return True
        else:
            logger.warning("No model-parameter relationships to insert")
            return False
    
    except Exception as e:
        logger.error(f"Database error in initialize_model_parameters: {e}", exc_info=True)
        return False


def get_model_parameters_mapping() -> dict:
    """
    Define which parameters each model supports with their data quality
    
    Returns:
        Dictionary mapping model_code to list of (parameter_code, data_quality) tuples
    
    Structure:
        {
            "MODEL_CODE": [
                ("parameter_code", "data_quality"),
                ...
            ]
        }
    
    Data Quality Levels:
    - "high": Direct measurement or high-resolution model output
    - "medium": Standard model output
    - "low": Degraded resolution or less reliable
    - "interpolated": Derived from other parameters
    
    Note: All parameters from the same model typically have the same quality,
    but we differentiate based on:
    - Direct measurements vs derived values
    - Core parameters vs secondary parameters
    - Spatial/temporal resolution considerations
    """
    
    return {
        # ==================== OM_FORECAST (Weather) ====================
        "OM_FORECAST": [
            # Core weather parameters - high quality
            ("temp_2m", "high"),
            ("humidity_2m", "high"),
            ("precip", "high"),
            ("weather_code", "high"),
            ("wind_speed_10m", "high"),
            ("wind_dir_10m", "high"),
            
            # Derived parameters - medium quality
            ("apparent_temp", "medium"),
            ("cloud_cover", "medium"),
            ("precip_prob", "medium"),
            
            # Daily aggregations - high quality
            ("temp_2m_max", "high"),
            ("temp_2m_min", "high"),
            ("precip_sum", "high"),
            ("precip_hours", "high"),
            ("precip_prob_max", "medium"),
            ("sunshine_duration", "high"),
            ("uv_index_max", "high"),
            ("wind_speed_10m_max", "high"),
            ("wind_gusts_10m_max", "high"),
            ("wind_dir_10m_dominant", "high"),
        ],
        
        # ==================== CAMS_EUROPE (Air Quality) ====================
        "CAMS_EUROPE": [
            # Direct pollutant measurements - high quality
            ("pm2_5", "high"),
            ("pm10", "high"),
            ("no2", "high"),
            ("o3", "high"),
            ("so2", "high"),
            ("co", "high"),
            
            # Derived/computed values - medium quality
            ("aqi_european", "medium"),
            ("aqi_us", "medium"),
            ("dust", "medium"),
            ("nh3", "medium"),
        ],
        
        # ==================== ECMWF_WAVES (Marine) ====================
        "ECMWF_WAVES": [
            # Primary wave parameters - high quality
            ("wave_height", "high"),
            ("wave_direction", "high"),
            ("wave_period", "high"),
            ("swell_wave_height", "high"),
            ("swell_wave_direction", "high"),
            ("swell_wave_period", "high"),
            
            # Derived wave components - medium quality
            ("wind_wave_height", "medium"),
            
            # Ocean parameters - high quality
            ("sea_temp", "high"),
            ("ocean_current_vel", "high"),
            ("ocean_current_dir", "high"),
            
            # Daily aggregations - high quality
            ("wave_height_max", "high"),
            ("wave_direction_dominant", "high"),
            ("wave_period_max", "high"),
            ("swell_wave_height_max", "high"),
            ("swell_wave_direction_dominant", "high"),
        ],
        
        # ==================== CAMS_SOLAR (Satellite Radiation) ====================
        "CAMS_SOLAR": [
            # Satellite-derived radiation - high quality (15-minute resolution)
            ("shortwave_rad", "high"),
            ("direct_rad", "high"),
            ("diffuse_rad", "high"),
            ("dni", "high"),
            
            # Computed radiation values - medium quality
            ("gti", "medium"),
            ("terrestrial_rad", "medium"),
        ],
        
        # ==================== EC_Earth3P_HR (Climate Projections) ====================
        "EC_Earth3P_HR": [
            # Climate model projections - medium quality (long-term forecasts)
            ("temp_2m_max", "medium"),
            ("temp_2m_min", "medium"),
            ("temp_2m_mean", "medium"),
            ("precip_sum", "medium"),
            ("precip_rain_sum", "medium"),
            ("precip_snow_sum", "medium"),
            ("humidity_2m_max", "medium"),
            ("humidity_2m_min", "medium"),
            ("humidity_2m_mean", "medium"),
            ("wind_speed_10m_mean", "medium"),
            ("wind_speed_10m_max", "medium"),
            ("pressure_msl_mean", "medium"),
            ("cloud_cover_mean", "medium"),
            ("radiation_shortwave_sum", "medium"),
            
            # Soil parameters - low quality (harder to predict long-term)
            ("soil_moisture_0_10cm", "low"),
        ],
    }


if __name__ == "__main__":
    main()
