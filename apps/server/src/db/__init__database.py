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
from src.services.weather_service import WeatherService
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
        
        if exist_weather_models > 1:
            # Initialize weather models
            print("Initializing weather models...")
            if initialize_weather_models(db):
                print("✓ Weather models initialized\n")
            else:
                print("✗ Failed to initialize weather models\n")
        
        if exist_weather_parameters > 1:
            # Initialize weather parameters
            print("Initializing weather parameters...")
            if initialize_weather_parameters(db):
                print("✓ Weather parameters initialized\n")
            else:
                print("✗ Failed to initialize weather parameters\n")
        
        if exist_model_parameters > 1:        
            # Initialize model_parameters
            if initialize_model_parameters(db):
                print("✓ Models parameters initialized\n")
            else:
                print("✗ Failed to initialize weather parameters\n")
        
        print("="*60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*60)
    
    finally:
       db.disconnect()
        
def initialize_model_parameters(db) -> bool:
    return


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
            logger.error(f"Database error in {"initialize weather_models_data"}: {e}")
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
            logger.error(f"Database error in {"initialize weather_parameters"}: {e}")
            return False
    
        

if __name__ == "__main__":
    main()