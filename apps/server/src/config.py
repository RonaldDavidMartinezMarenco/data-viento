import os
from pathlib import Path
from dotenv import load_dotenv

config_dir = Path(__file__).parent 
env_path = config_dir.parent / '.env'


print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

load_dotenv(env_path)

class Config:
    """
    Configuration class that reads all environment variables
    from the .env file and stores them as class attributes
    """
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'data_viento_database')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 10))
    
# Create a single instance of Config to use throughout the app
config = Config()
