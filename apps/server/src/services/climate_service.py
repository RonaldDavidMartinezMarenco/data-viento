"""
Climate Service

Handles climate change projection operations:
1. Fetch climate data from Open-Meteo Climate API
2. Parse responses using Pydantic models
3. Insert data into database (climate_projections + climate_daily)

Maps to tables:
- climate_projections (metadata: model, date range, location)
- climate_daily (daily values: temperature, precipitation, etc.)

Note: Climate API provides historical + future projections from climate models
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional, Dict, Any, List
from src.services.base_service import BaseService
from src.services.location_service import LocationService
from src.models.climate_models import ClimateResponse
from src.db.database import DatabaseConnection


class ClimateService(BaseService):
    """
    Service for climate projection operations
    
    Workflow:
    1. Fetch climate data from Open-Meteo Climate API
    2. Parse with Pydantic models (validation)
    3. Get/create location
    4. Get/create climate model
    5. Create climate projection record (metadata)
    6. Insert daily climate data (temperature, precipitation, etc.)
    
    Special Features:
    - Handles date ranges (start_date to end_date)
    - Supports multiple climate models (CMCC, MRI, etc.)
    - Can fetch historical OR future projections
    - Stores daily aggregates (no hourly data)
    """
    
    def __init__(self, db: Optional[DatabaseConnection] = None):
        """Initialize climate service"""
        super().__init__(db)
        self.location_service = LocationService(self.db)
        # Note: Climate has multiple models, we get model_id per request
    
    
    def _get_or_create_climate_model(self, model_code: str) -> int:
        """
        Get or create climate model
        
        Args:
            model_code: Model code (e.g., 'CMCC_CM2_VHR4', 'MRI_AGCM3_2_S')
        
        Returns:
            model_id for the climate model
        
        Explanation:
        - Climate API supports multiple models (CMCC, MRI, EC_Earth3P_HR, etc.)
        - Each model has different characteristics
        - We create model records dynamically based on API usage
        
        Available models:
        - CMCC_CM2_VHR4: Italian climate model (4km resolution)
        - MRI_AGCM3_2_S: Japanese climate model
        - EC_Earth3P_HR: European climate model
        - FGOALS_f3_H: Chinese climate model
        - HiRAM_SIT_HR: US climate model
        - NICAM_AMIP: Japanese non-hydrostatic model
        """
        
        # Check if model exists
        query = "SELECT model_id FROM weather_models WHERE model_code = %s"
        result = self.db.execute_query(query, (model_code,))
        
        if result:
            return result[0][0]
        
        # Model metadata mapping
        model_metadata = {
            'CMCC_CM2_VHR4': {
                'name': 'CMCC-CM2-VHR4',
                'provider': 'CMCC Foundation',
                'country': 'Italy',
                'resolution_km': 25.0,
                'description': 'Italian Earth System Model - Very High Resolution (25km)'
            },
            'MRI_AGCM3_2_S': {
                'name': 'MRI-AGCM3.2-S',
                'provider': 'Meteorological Research Institute',
                'country': 'Japan',
                'resolution_km': 20.0,
                'description': 'Japanese Atmospheric GCM - Super High Resolution (20km)'
            },
            'EC_Earth3P_HR': {
                'name': 'EC-Earth3P-HR',
                'provider': 'EC-Earth Consortium',
                'country': 'European Union',
                'resolution_km': 29.0,
                'description': 'European Earth System Model - High Resolution (25km)'
            },
            'FGOALS_f3_H': {
                'name': 'FGOALS-f3-H',
                'provider': 'Chinese Academy of Sciences',
                'country': 'China',
                'resolution_km': 28.0,
                'description': 'Chinese Climate System Model - High Resolution (28km)'
            },
            'HiRAM_SIT_HR': {
                'name': 'HiRAM-SIT-HR',
                'provider': 'NOAA GFDL',
                'country': 'USA',
                'resolution_km': 25.0,
                'description': 'US High Resolution Atmospheric Model (25km)'
            },
            'NICAM_AMIP': {
                'name': 'NICAM16-8S',
                'provider': 'JAMSTEC',
                'country': 'Japan',
                'resolution_km': 31.0,
                'description': 'Japanese Non-hydrostatic Icosahedral Model (14km)'
            }
        }
        
        # Get metadata or use defaults
        metadata = model_metadata.get(model_code, {
            'name': model_code,
            'provider': 'Open-Meteo',
            'country': 'Unknown',
            'resolution_km': 25.0,
            'description': f'Climate model {model_code}'
        })
        
        # Create model
        query = """
        INSERT INTO weather_models (
            model_code, model_name, provider, provider_country,
            resolution_km, resolution_degrees, forecast_days, update_frequency_hours,
            temporal_resolution, geographic_coverage, model_type,
            is_active, description, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        """
        
        params = (
            model_code,
            metadata['name'],
            metadata['provider'],
            metadata['country'],
            metadata['resolution_km'],
            metadata['resolution_km'] / 111.0,  # Convert km to degrees (approx)
            0,  # forecast_days (not applicable for climate)
            0,  # update_frequency_hours (historical/projection data)
            'daily',
            'global',
            'climate',
            True,
            metadata['description'],
        )
        
        model_id = self.db.execute_insert(query, params)
        self.logger.info(f"✓ Created climate model: {model_code} (ID: {model_id})")
        return model_id
    
    
    async def fetch_and_save_climate_data(
        self,
        location_name: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        model: str = 'EC_Earth3P_HR',
        disable_bias_correction: bool = False,
        cell_selection : str = 'land',
        **location_kwargs
    ) -> Dict[str, Any]:
        """
        Complete workflow: Fetch climate data from API and save to database
        
        Args:
            location_name: Location name (e.g., "Madrid")
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            start_date: Start date (YYYY-MM-DD) - can be past or future
            end_date: End date (YYYY-MM-DD) - can be past or future
            model: Climate model code (default: 'CMCC_CM2_VHR4')
            disable_bias_correction: Disable bias correction (default: False)
            cell_selection: Cell selection method ('land', 'sea', 'nearest')
            **location_kwargs: Additional location fields (timezone, country, etc.)
        
        Returns:
            Dictionary with operation results
        
        Example:
            >>> climate_service = ClimateService()
            >>> # Fetch historical climate data (1950-2000)
            >>> result = await climate_service.fetch_and_save_climate_data(
            ...     "Madrid",
            ...     40.4168,
            ...     -3.7038,
            ...     start_date="1950-01-01",
            ...     end_date="2000-12-31",
            ...     model="CMCC_CM2_VHR4",
            ...     timezone="Europe/Madrid"
            ... )
            >>> 
            >>> # Fetch future climate projections (2050-2100)
            >>> result = await climate_service.fetch_and_save_climate_data(
            ...     "Madrid",
            ...     40.4168,
            ...     -3.7038,
            ...     start_date="2050-01-01",
            ...     end_date="2100-12-31",
            ...     model="MRI_AGCM3_2_S"
            ... )
        
        Note:
        - start_date and end_date are REQUIRED (no defaults)
        - Can fetch past (historical) or future (projections)
        - Date range is limited by model (typically 1950-2100)
        - Climate data is ALWAYS daily (no hourly)
        """
        
        result = {
            'success': False,
            'location_id': None,
            'climate_id': None,
            'daily_saved': False,
            'days_saved': 0,
            'error': None
        }
        
        try:
            self.logger.info(
                f"Fetching climate data for {location_name} "
                f"({start_date} to {end_date}, model: {model})"
            )
            
            # Step 1: Fetch data from API
            api_response = await self.api_client.get_climate_projection(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                models=model,
                timezone=location_kwargs.get('timezone', 'auto')
            )
            
            if not api_response:
                result['error'] = 'Failed to fetch data from API'
                return result
            
            # Step 2: Parse response with Pydantic model (validates data)
            climate_response = ClimateResponse(**api_response)
            self.logger.info(f"✓ API data validated successfully")
            
            if not climate_response.daily:
                result['error'] = 'No daily climate data available'
                return result
            
            # Step 3: Get or create location
            location_id = self.location_service.get_or_create_location(
                name=location_name,
                latitude=latitude,
                longitude=longitude,
                **location_kwargs
            )
            result['location_id'] = location_id
            
            # Step 4: Get or create climate model
            model_id = self._get_or_create_climate_model(model)
            
            # Step 5: Create climate projection record (metadata)
            climate_id = self._create_climate_projection(
                location_id=location_id,
                model_id=model_id,
                start_date=start_date,
                end_date=end_date,
                disable_bias_correction=disable_bias_correction,
                cell_selection=cell_selection,
                metadata=climate_response
            )
            
            if climate_id is None:
                result['error'] = 'Failed to create climate projection record'
                return result
            
            result['climate_id'] = climate_id
            
            # Step 6: Save daily climate data
            daily_saved = self._save_daily_climate_data(
                climate_id=climate_id,
                daily_data=climate_response.daily
            )
            
            result['daily_saved'] = daily_saved
            result['days_saved'] = len(climate_response.daily.time) if daily_saved else 0
            result['success'] = True
            
            self.logger.info(
                f"✓ Climate data saved successfully for {location_name} "
                f"({result['days_saved']} days)"
            )
        
        except Exception as e:
            self.logger.error(f"✗ Error in fetch_and_save_climate_data: {e}", exc_info=True)
            result['error'] = str(e)
        
        return result
    
    
    def _create_climate_projection(
        self,
        location_id: int,
        model_id: int,
        start_date: str,
        end_date: str,
        disable_bias_correction: bool,
        cell_selection: str,
        metadata
    ) -> Optional[int]:
        """
        Create climate projection record (metadata table)
        
        Schema mapping (climate_projections):
        - climate_id (PK, AUTO_INCREMENT)
        - location_id (FK to locations)
        - model_id (FK to weather_models)
        - start_date (DATE)
        - end_date (DATE)
        - disable_bias_correction (BOOLEAN)
        - cell_selection (ENUM: 'land', 'sea', 'nearest')
        - generation_time_ms (DECIMAL)
        - timezone (VARCHAR)
        - utc_offset_seconds (INTEGER)
        - created_at (TIMESTAMP)
        - UNIQUE KEY: (location_id, model_id, start_date, end_date)
        
        Args:
            location_id: Location ID
            model_id: Model ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            disable_bias_correction: Bias correction disabled flag
            cell_selection: Cell selection method
            metadata: ClimateResponse Pydantic model
        
        Returns:
            climate_id (projection record ID)
        
        Explanation:
        - Creates ONE projection record per (location, model, date_range)
        - Stores metadata (generation time, timezone, etc.)
        - ON DUPLICATE KEY UPDATE returns existing climate_id
        - Daily data links to this record via climate_id FK
        """
        
        query = """
        INSERT INTO climate_projections (
            location_id, model_id, start_date, end_date,
            disable_bias_correction, cell_selection,
            generation_time_ms, timezone, utc_offset_seconds,
            created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON DUPLICATE KEY UPDATE
            generation_time_ms = VALUES(generation_time_ms),
            timezone = VALUES(timezone),
            utc_offset_seconds = VALUES(utc_offset_seconds),
            created_at = NOW()
        """
        
        params = (
            location_id,
            model_id,
            start_date,
            end_date,
            disable_bias_correction,
            cell_selection,
            metadata.generationtime_ms,
            metadata.timezone,
            metadata.utc_offset_seconds,
        )
        
        try:
            climate_id = self.db.execute_insert(query, params)
            
            # If ON DUPLICATE KEY UPDATE triggered, get existing climate_id
            if climate_id == 0:
                select_query = """
                SELECT climate_id FROM climate_projections
                WHERE location_id = %s AND model_id = %s 
                  AND start_date = %s AND end_date = %s
                """
                result = self.db.execute_query(
                    select_query, 
                    (location_id, model_id, start_date, end_date)
                )
                climate_id = result[0][0] if result else None
            
            self.logger.info(
                f"✓ Climate projection created: ID {climate_id} "
                f"(location {location_id}, model {model_id}, {start_date} to {end_date})"
            )
            return climate_id
        
        except Exception as e:
            self._log_db_error("create_climate_projection", e)
            return None
    
    def _save_daily_climate_data(
        self,
        climate_id: int,
        daily_data
    ) -> bool:
        """
        Save daily climate data to database
        
        Schema mapping (climate_daily):
        - data_id (PK, AUTO_INCREMENT)
        - climate_id (FK to climate_projections)
        - valid_date (DATE)
        - temperature_2m_max (DECIMAL)
        - temperature_2m_min (DECIMAL)
        - temperature_2m_mean (DECIMAL)
        - precipitation_sum (DECIMAL)
        - rain_sum (DECIMAL)
        - snowfall_sum (DECIMAL)
        - relative_humidity_2m_max (DECIMAL)
        - relative_humidity_2m_min (DECIMAL)
        - relative_humidity_2m_mean (DECIMAL)
        - wind_speed_10m_mean (DECIMAL)
        - wind_speed_10m_max (DECIMAL)
        - pressure_msl_mean (DECIMAL)
        - cloud_cover_mean (DECIMAL)
        - shortwave_radiation_sum (DECIMAL)
        - soil_moisture_0_to_10cm_mean (DECIMAL)
        - UNIQUE KEY: (climate_id, valid_date)
        
        Args:
            climate_id: Climate projection ID
            daily_data: ClimateDaily Pydantic model
        
        Returns:
            True if saved successfully
        
        Explanation:
        - Saves multiple days (each day is a separate row)
        - Uses bulk insert for efficiency
        - ON DUPLICATE KEY UPDATE for idempotency
        - All columns match schema exactly (including _mean, _sum suffixes)
        """
        
        if not daily_data.time:
            return False
        
        query = """
        INSERT INTO climate_daily (
            climate_id, valid_date,
            temperature_2m_max, temperature_2m_min, temperature_2m_mean,
            precipitation_sum, rain_sum, snowfall_sum,
            relative_humidity_2m_max, relative_humidity_2m_min, relative_humidity_2m_mean,
            wind_speed_10m_mean, wind_speed_10m_max,
            pressure_msl_mean, cloud_cover_mean,
            shortwave_radiation_sum, soil_moisture_0_to_10cm_mean
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            temperature_2m_max = VALUES(temperature_2m_max),
            temperature_2m_min = VALUES(temperature_2m_min),
            temperature_2m_mean = VALUES(temperature_2m_mean),
            precipitation_sum = VALUES(precipitation_sum),
            rain_sum = VALUES(rain_sum),
            snowfall_sum = VALUES(snowfall_sum),
            relative_humidity_2m_max = VALUES(relative_humidity_2m_max),
            relative_humidity_2m_min = VALUES(relative_humidity_2m_min),
            relative_humidity_2m_mean = VALUES(relative_humidity_2m_mean),
            wind_speed_10m_mean = VALUES(wind_speed_10m_mean),
            wind_speed_10m_max = VALUES(wind_speed_10m_max),
            pressure_msl_mean = VALUES(pressure_msl_mean),
            cloud_cover_mean = VALUES(cloud_cover_mean),
            shortwave_radiation_sum = VALUES(shortwave_radiation_sum),
            soil_moisture_0_to_10cm_mean = VALUES(soil_moisture_0_to_10cm_mean)
        """
        
        # Prepare bulk data
        rows = []
        for i, date in enumerate(daily_data.time):
            row = (
                climate_id,
                date,  # valid_date
                # Temperature
                daily_data.temperature_2m_max[i] if daily_data.temperature_2m_max and i < len(daily_data.temperature_2m_max) else None,
                daily_data.temperature_2m_min[i] if daily_data.temperature_2m_min and i < len(daily_data.temperature_2m_min) else None,
                daily_data.temperature_2m_mean[i] if daily_data.temperature_2m_mean and i < len(daily_data.temperature_2m_mean) else None,
                # Precipitation
                daily_data.precipitation_sum[i] if daily_data.precipitation_sum and i < len(daily_data.precipitation_sum) else None,
                daily_data.rain_sum[i] if daily_data.rain_sum and i < len(daily_data.rain_sum) else None,
                daily_data.snowfall_sum[i] if daily_data.snowfall_sum and i < len(daily_data.snowfall_sum) else None,
                # Humidity
                daily_data.relative_humidity_2m_max[i] if daily_data.relative_humidity_2m_max and i < len(daily_data.relative_humidity_2m_max) else None,
                daily_data.relative_humidity_2m_min[i] if daily_data.relative_humidity_2m_min and i < len(daily_data.relative_humidity_2m_min) else None,
                daily_data.relative_humidity_2m_mean[i] if daily_data.relative_humidity_2m_mean and i < len(daily_data.relative_humidity_2m_mean) else None,
                # Wind
                daily_data.wind_speed_10m_mean[i] if daily_data.wind_speed_10m_mean and i < len(daily_data.wind_speed_10m_mean) else None,
                daily_data.wind_speed_10m_max[i] if daily_data.wind_speed_10m_max and i < len(daily_data.wind_speed_10m_max) else None,
                # Pressure
                daily_data.pressure_msl_mean[i] if daily_data.pressure_msl_mean and i < len(daily_data.pressure_msl_mean) else None,
                # Cloud cover
                daily_data.cloud_cover_mean[i] if daily_data.cloud_cover_mean and i < len(daily_data.cloud_cover_mean) else None,
                # Solar radiation
                daily_data.shortwave_radiation_sum[i] if daily_data.shortwave_radiation_sum and i < len(daily_data.shortwave_radiation_sum) else None,
                # Soil moisture
                daily_data.soil_moisture_0_to_10cm_mean[i] if daily_data.soil_moisture_0_to_10cm_mean and i < len(daily_data.soil_moisture_0_to_10cm_mean) else None,
            )
            rows.append(row)
        
        try:
            rows_inserted = self.db.execute_bulk_insert(query, rows)
            self.logger.info(
                f"✓ Daily climate data saved: {rows_inserted} days for climate_id {climate_id}"
            )
            return True
        except Exception as e:
            self._log_db_error("save_daily_climate_data", e)
            return False
        
    def get_climate_data(
        self,
        location_id: int,
        model_code: str,
        start_date: str,
        end_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get climate data for a location, model, and date range
        
        Args:
            location_id: Location ID
            model_code: Climate model code (e.g., 'CMCC_CM2_VHR4')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with climate projection and daily data, or None
        
        Example Output:
            {
                'climate_id': 1,
                'location_id': 1,
                'model_code': 'CMCC_CM2_VHR4',
                'start_date': '2050-01-01',
                'end_date': '2050-12-31',
                'total_days': 365,
                'daily_data': [
                    {
                        'valid_date': '2050-01-01',
                        'temperature_2m_max': 15.2,
                        'temperature_2m_min': 5.8,
                        'precipitation_sum': 2.5,
                        ...
                    },
                    ...
                ]
            }
        """
        
        try:
            # Get climate projection
            projection_query = """
            SELECT cp.climate_id, cp.start_date, cp.end_date,
                   cp.disable_bias_correction, cp.cell_selection,
                   wm.model_code, wm.model_name
            FROM climate_projections cp
            JOIN weather_models wm ON cp.model_id = wm.model_id
            WHERE cp.location_id = %s 
              AND wm.model_code = %s
              AND cp.start_date = %s
              AND cp.end_date = %s
            """
            
            projection = self.db.execute_query(
                projection_query,
                (location_id, model_code, start_date, end_date)
            )
            
            if not projection:
                return None
            
            climate_id = projection[0][0]
            
            # Get daily data
            daily_query = """
            SELECT valid_date,
                   temperature_2m_max, temperature_2m_min, temperature_2m_mean,
                   precipitation_sum, rain_sum, snowfall_sum,
                   relative_humidity_2m_max, relative_humidity_2m_min, relative_humidity_2m_mean,
                   wind_speed_10m_mean, wind_speed_10m_max,
                   pressure_msl_mean, cloud_cover_mean,
                   shortwave_radiation_sum, soil_moisture_0_to_10cm_mean
            FROM climate_daily
            WHERE climate_id = %s
            ORDER BY valid_date
            """
            
            daily_results = self.db.execute_query(daily_query, (climate_id,))
            
            daily_data = []
            for row in daily_results:
                daily_data.append({
                    'valid_date': row[0],
                    'temperature_2m_max': float(row[1]) if row[1] else None,
                    'temperature_2m_min': float(row[2]) if row[2] else None,
                    'temperature_2m_mean': float(row[3]) if row[3] else None,
                    'precipitation_sum': float(row[4]) if row[4] else None,
                    'rain_sum': float(row[5]) if row[5] else None,
                    'snowfall_sum': float(row[6]) if row[6] else None,
                    'relative_humidity_2m_max': float(row[7]) if row[7] else None,
                    'relative_humidity_2m_min': float(row[8]) if row[8] else None,
                    'relative_humidity_2m_mean': float(row[9]) if row[9] else None,
                    'wind_speed_10m_mean': float(row[10]) if row[10] else None,
                    'wind_speed_10m_max': float(row[11]) if row[11] else None,
                    'pressure_msl_mean': float(row[12]) if row[12] else None,
                    'cloud_cover_mean': float(row[13]) if row[13] else None,
                    'shortwave_radiation_sum': float(row[14]) if row[14] else None,
                    'soil_moisture_0_to_10cm_mean': float(row[15]) if row[15] else None,
                })
            
            return {
                'climate_id': climate_id,
                'location_id': location_id,
                'model_code': projection[0][5],
                'model_name': projection[0][6],
                'start_date': projection[0][1],
                'end_date': projection[0][2],
                'disable_bias_correction': projection[0][3],
                'cell_selection': projection[0][4],
                'total_days': len(daily_data),
                'daily_data': daily_data
            }
        
        except Exception as e:
            self._log_db_error("get_climate_data", e)
            return None
    def get_climate_statistics(
        self,
        location_id: int,
        model_code: str,
        start_date: str,
        end_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregated climate statistics for a date range
        
        Args:
            location_id: Location ID
            model_code: Climate model code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with statistics or None
        
        Example Output:
            {
                'location_id': 1,
                'model_code': 'CMCC_CM2_VHR4',
                'period': '2050-01-01 to 2050-12-31',
                'avg_temp_max': 18.5,
                'avg_temp_min': 8.2,
                'avg_temp_mean': 13.4,
                'total_precipitation': 650.5,
                'total_rain': 580.2,
                'total_snowfall': 70.3,
                'avg_humidity': 65.5,
                'avg_wind_speed': 12.3,
                'total_days': 365
            }
        """
        
        try:
            query = """
            SELECT 
                COUNT(*) as total_days,
                AVG(temperature_2m_max) as avg_temp_max,
                AVG(temperature_2m_min) as avg_temp_min,
                AVG(temperature_2m_mean) as avg_temp_mean,
                SUM(precipitation_sum) as total_precipitation,
                SUM(rain_sum) as total_rain,
                SUM(snowfall_sum) as total_snowfall,
                AVG(relative_humidity_2m_mean) as avg_humidity,
                AVG(wind_speed_10m_mean) as avg_wind_speed,
                AVG(pressure_msl_mean) as avg_pressure,
                AVG(cloud_cover_mean) as avg_cloud_cover,
                SUM(shortwave_radiation_sum) as total_radiation
            FROM climate_daily cd
            JOIN climate_projections cp ON cd.climate_id = cp.climate_id
            JOIN weather_models wm ON cp.model_id = wm.model_id
            WHERE cp.location_id = %s
              AND wm.model_code = %s
              AND cp.start_date = %s
              AND cp.end_date = %s
            """
            
            result = self.db.execute_query(
                query,
                (location_id, model_code, start_date, end_date)
            )
            
            if not result or not result[0][0]:
                return None
            
            row = result[0]
            
            return {
                'location_id': location_id,
                'model_code': model_code,
                'period': f"{start_date} to {end_date}",
                'total_days': row[0],
                'avg_temp_max': round(float(row[1]), 2) if row[1] else None,
                'avg_temp_min': round(float(row[2]), 2) if row[2] else None,
                'avg_temp_mean': round(float(row[3]), 2) if row[3] else None,
                'total_precipitation': round(float(row[4]), 2) if row[4] else None,
                'total_rain': round(float(row[5]), 2) if row[5] else None,
                'total_snowfall': round(float(row[6]), 2) if row[6] else None,
                'avg_humidity': round(float(row[7]), 2) if row[7] else None,
                'avg_wind_speed': round(float(row[8]), 2) if row[8] else None,
                'avg_pressure': round(float(row[9]), 2) if row[9] else None,
                'avg_cloud_cover': round(float(row[10]), 2) if row[10] else None,
                'total_radiation': round(float(row[11]), 2) if row[11] else None,
            }
        
        except Exception as e:
            self._log_db_error("get_climate_statistics", e)
            return None
        
    def list_available_projections(
        self,
        location_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        List all available climate projections for a location
        
        Args:
            location_id: Location ID
        
        Returns:
            List of projection summaries or None
        
        Example Output:
            [
                {
                    'climate_id': 1,
                    'model_code': 'CMCC_CM2_VHR4',
                    'model_name': 'CMCC-CM2-VHR4',
                    'start_date': '2050-01-01',
                    'end_date': '2050-12-31',
                    'total_days': 365
                },
                ...
            ]
        """
        
        try:
            query = """
            SELECT 
                cp.climate_id,
                wm.model_code,
                wm.model_name,
                cp.start_date,
                cp.end_date,
                COUNT(cd.data_id) as total_days
            FROM climate_projections cp
            JOIN weather_models wm ON cp.model_id = wm.model_id
            LEFT JOIN climate_daily cd ON cp.climate_id = cd.climate_id
            WHERE cp.location_id = %s
            GROUP BY cp.climate_id, wm.model_code, wm.model_name, cp.start_date, cp.end_date
            ORDER BY cp.start_date DESC
            """
            
            results = self.db.execute_query(query, (location_id,))
            
            if not results:
                return None
            
            projections = []
            for row in results:
                projections.append({
                    'climate_id': row[0],
                    'model_code': row[1],
                    'model_name': row[2],
                    'start_date': row[3],
                    'end_date': row[4],
                    'total_days': row[5]
                })
            
            return projections
        
        except Exception as e:
            self._log_db_error("list_available_projections", e)
            return None