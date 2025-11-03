"""
Air Quality Service

Handles air quality operations:
1. Fetch air quality data from Open-Meteo Air Quality API
2. Parse responses using Pydantic models
3. Insert data into database (air_quality_current, air_quality_forecasts, air_quality_data)

Maps to tables:
- air_quality_current (stores latest air quality readings per location)
- air_quality_forecasts (metadata for hourly forecast batches)
- air_quality_data (individual hourly forecast data points)

"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional, Dict, Any, List
from src.services.base_service import BaseService
from src.services.location_service import LocationService
from src.models.air_quality_models import AirQualityResponse
from src.db.database import DatabaseConnection


class AirQualityService(BaseService):
    """
    Air Quality Service
    
    Fetches and stores air quality data from Open-Meteo Air Quality API

    Workflow:
    1. Fetch current/hourly data from API
    2. Validate with Pydantic models
    3. Get or create location in database
    4. Get model_id for CAMS_EUROPE
    5. Save current air quality (if requested)
    6. Save hourly forecast (if requested)
    """
    
    def __init__(self, db: Optional[DatabaseConnection] = None):
        """
        Initialize Air Quality Service
        """
        super().__init__(db)
        self.location_service = LocationService(self.db)
        self.model_id = self._get_or_create_air_quality_model()
        
    def _get_or_create_air_quality_model(self) -> int:
        """
        Get or create air quality model for CAMS Europe
        
        Returns:
            model_id for CAMS_EUROPE
        
        Explanation:
        - Checks if CAMS_EUROPE model exists
        - If not, creates it with metadata
        - Returns model_id for use in all air quality inserts
        """
        
        # Check if model exists
        query = "SELECT model_id FROM weather_models WHERE model_code = 'CAMS_EUROPE'"
        result = self.db.execute_query(query)
        
        if result:
            return result[0][0]
        
        # Create model if not exists
        query = """
        INSERT INTO weather_models (
            model_code, model_name, provider, provider_country,
            resolution_km, resolution_degrees, forecast_days, update_frequency_hours,
            temporal_resolution, geographic_coverage, model_type,
            is_active, description, created_at
        ) VALUES (
            'CAMS_EUROPE', 'CAMS Europe Air Quality Model', 'Copernicus', 'European Union',
            10.0, 0.1, 5, 6, 'hourly', 'regional', 'air_quality',
            TRUE, 'CAMS Europe air quality forecasts. PM2.5, PM10, and pollutants.', NOW()
        )
        """
        
        model_id = self.db.execute_insert(query)
        self.logger.info(f"✓ Created air quality model: CAMS_EUROPE (ID: {model_id})")
        return model_id
        
    async def fetch_and_save_air_quality(
        self,
        location_name: str,
        latitude: float,
        longitude: float,
        include_current: bool = True,
        include_hourly: bool = False,
        forecast_days: int = 5,
        domains: str = "auto",
        **location_kwargs
    ) -> Dict[str, Any]:
        """
        Fetch and save air quality data for a location
        
        Args:
            location_name: Name of the location
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            include_current: Fetch current air quality
            include_hourly: Fetch hourly forecast
            forecast_days: Number of forecast days (1-5)
            domains: Data domain ('cams_europe', 'cams_global', 'auto')
            **location_kwargs: Additional location fields (timezone, country, etc.)
        
        Returns:
            Dictionary with success status and saved counts
        """
        
        result = {
            'success': False,
            'location_id': None,
            'current_saved': False,
            'hourly_saved': False,
            'error': None
        }
        
        try:
            self.logger.info(f"Fetching Air_Quality data for {location_name} ({latitude}, {longitude})")
            
            # Fetch data
            api_response = await self.api_client.get_air_quality(
                latitude=latitude,
                longitude=longitude,
                include_current=include_current,
                include_hourly=include_hourly,
                timezone=location_kwargs.get('timezone','auto'),
                forecast_days=forecast_days 
            )
            
            if not api_response:
                result['error'] = 'Failed to fetch data from API'
                return result
            
            # Step 2: Parse response with Pydantic model (validates data)
            aq_response = AirQualityResponse(**api_response)
            self.logger.info(f"✓ API data validated successfully")
            
            # Step 3: Get or create location
            location_id = self.location_service.get_or_create_location(
                name = location_name,
                latitude=latitude,
                longitude=longitude,
                **location_kwargs
            )
            result ['location_id'] = location_id
            
            # Step 4: Save Current air Quality or Hourly
            if include_current and aq_response.current:
                current_saved = self._save_current_air_quality(
                    location_id=location_id,
                    current_data=aq_response.current
                )
                result ['current_saved'] = current_saved
            
            if include_hourly and aq_response.hourly:
                hourly_saved = self._save_hourly_forecast(
                    location_id,
                    aq_response.hourly,
                    aq_response
                )
                result ['hourly_saved'] = hourly_saved
                
            result['success'] = True
                
            
        except Exception as e:
            self.logger.error(f"✗ Error in fetch_and_save_air_quality: {e}")
            result['error'] = str(e)
        
        return result
    
    def _save_current_air_quality(
        self,
        location_id: int,
        current_data
    ) -> bool:
        """
            Save current air_quality data to database
            
            Maps to: air_quality_current table
            
            Args:
                location_id: Location ID
                current_data: AirQualityCurrent Pydantic model
            
            Returns:
                True if saved successfully
            
            Explanation:
            - Uses ON DUPLICATE KEY UPDATE to update existing row
            - Only one current weather record per location
            - Automatically updates if newer data arrives
        """
        query = """
        INSERT INTO air_quality_current (
            location_id, observation_time,
            pm2_5, pm10, european_aqi, us_aqi,
            nitrogen_dioxide, ozone, sulphur_dioxide, carbon_monoxide,
            dust, ammonia, updated_at
        ) VALUES (
            %s, NOW(),
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, NOW()
        )
        ON DUPLICATE KEY UPDATE
            observation_time = NOW(),
            pm2_5 = VALUES(pm2_5),
            pm10 = VALUES(pm10),
            european_aqi = VALUES(european_aqi),
            us_aqi = VALUES(us_aqi),
            nitrogen_dioxide = VALUES(nitrogen_dioxide),
            ozone = VALUES(ozone),
            sulphur_dioxide = VALUES(sulphur_dioxide),
            carbon_monoxide = VALUES(carbon_monoxide),
            dust = VALUES(dust),
            ammonia = VALUES(ammonia),
            updated_at = NOW()
        """
        params = (
            location_id,
            current_data.pm2_5,
            current_data.pm10,
            current_data.european_aqi,
            current_data.us_aqi,
            current_data.nitrogen_dioxide,
            current_data.ozone,
            current_data.sulphur_dioxide,
            current_data.carbon_monoxide,
            current_data.dust,
            current_data.ammonia,
        )
        
        try:
            self.db.execute_insert(query, params)
            self.logger.info(f"✓ Current air quality saved for location {location_id}")
            return True
        except Exception as e:
            self._log_db_error("save_current_air_quality", e)
            return False
    
    def _save_hourly_forecast(
        self,
        location_id: int,
        hourly_data,
        aq_metadata,
    ) -> bool:
        
        if not hourly_data.time:
            self.logger.warning("No hourly data to save")
            return False
        
        try:
            forecast_query = """
            INSERT INTO air_quality_forecasts (
                location_id, model_id, forecast_reference_time,
                data_domain, generation_time_ms, timezone, utc_offset_seconds, created_at
            ) VALUES (
                %s, %s, NOW(), %s, %s, %s, %s, NOW()
            )
            """
            
            forecast_params = (
                location_id,
                self.model_id,
                getattr(aq_metadata, 'data_domain', 'auto'),
                aq_metadata.generationtime_ms,
                aq_metadata.timezone,
                aq_metadata.utc_offset_seconds,
            )

            forecast_id = self.db.execute_insert(forecast_query, forecast_params)
            
            if forecast_id <= 0:
                self.logger.error("Failed to create forecast batch")
                return False
            
            self.logger.info(f"✓ Created forecast air_quality batch ID: {forecast_id}")
            
            parameter_mapping = {
                'pm2_5': 'pm2_5',
                'pm10': 'pm10',
                'european_aqi': 'aqi_european',
                'us_aqi': 'aqi_us',
                'nitrogen_dioxide': 'no2',
                'ozone': 'o3',
                'sulphur_dioxide': 'so2',
                'carbon_monoxide': 'co',
            }
            # Step 3: Insert forecast data for each parameter
            total_rows = 0
            
            for api_field, param_code in parameter_mapping.items():
                # Get the data array from hourly_data
                data_array = getattr(hourly_data, api_field, None)
                
                if data_array is None:
                    continue
                
                # Get or create parameter_id
                parameter_id = self._get_or_create_parameter(param_code, api_field)
                
                if parameter_id is None:
                    self.logger.warning(f"Could not get parameter_id for {param_code}")
                    continue
                
                # Insert all hourly values for this parameter
                rows = self._insert_forecast_parameter_data(
                    forecast_id=forecast_id,
                    parameter_id=parameter_id,
                    time_array=hourly_data.time,
                    value_array=data_array,
                    param_code=param_code
                )
                
                total_rows += rows
            
            self.logger.info(
                f"✓ Hourly forecast saved: {total_rows} data points "
                f"({len(hourly_data.time)} hours x {len(parameter_mapping)} parameters) "
                f"for location {location_id}"
            )
            
            return True
        except Exception as e:
            self._log_db_error("save_hourly_forecast", e)
            return False
        
        
    def _insert_forecast_parameter_data(
        self,
        forecast_id: int,
        parameter_id: int,
        time_array: list,
        value_array: list,
        param_code: str
    ) -> int:
        
        # Get unit from weather_parameters
        unit_query = "SELECT unit FROM weather_parameters WHERE parameter_id = %s"
        unit_result = self.db.execute_query(unit_query, (parameter_id,))
        unit = unit_result[0][0] if unit_result else None
        
        # Prepare bulk insert
        insert_query = """
        INSERT IGNORE INTO air_quality_data (
            air_quality_id, parameter_id, valid_time, value,
            unit, aqi_category, health_impact, quality_flag
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        rows = []
        for i, timestamp in enumerate(time_array):
            
            # Get value (could be None)
            value = value_array[i] if i < len(value_array) else None
            
            row = (
                forecast_id,
                parameter_id,
                timestamp,          
                value,
                unit,
                'moderate',
                'high',                              
                'good',             
            )
            rows.append(row)
        
        # Execute bulk insert
        rows_inserted = self.db.execute_bulk_insert(insert_query, rows)
        
        return rows_inserted
    
    def cleanup_old_forecasts(self, days_to_keep: int = 7) -> int:
        """
        Delete old air quality forecast batches and their data
        
        Args:
            days_to_keep: Number of days to keep (default: 7)
        
        Returns:
            Number of forecast batches deleted
        
        Explanation:
        - Deletes forecast batches older than X days
        - Cascade deletes air_quality_data rows
        - Keeps database size manageable
        - Run this daily via cron job
        """
        
        try:
            # Step 1: Find old forecast IDs
            select_query = """
            SELECT air_quality_id, location_id, forecast_reference_time
            FROM air_quality_forecasts
            WHERE forecast_reference_time < DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            
            old_forecasts = self.db.execute_query(select_query, (days_to_keep,))
            
            if not old_forecasts:
                self.logger.info(f"No air quality forecasts older than {days_to_keep} days to delete")
                return 0
            
            forecast_ids = [row[0] for row in old_forecasts]
            
            # Step 2: Delete air_quality_data rows
            if forecast_ids:
                placeholders = ','.join(['%s'] * len(forecast_ids))
                delete_data_query = f"""
                DELETE FROM air_quality_data
                WHERE air_quality_id IN ({placeholders})
                """
                
                self.db.execute_query(delete_data_query, forecast_ids)
                self.logger.info(f"✓ Deleted air_quality_data for {len(forecast_ids)} batches")
            
            # Step 3: Delete forecast batches
            delete_forecast_query = f"""
            DELETE FROM air_quality_forecasts
            WHERE air_quality_id IN ({placeholders})
            """
            
            self.db.execute_query(delete_forecast_query, forecast_ids)
            
            self.logger.info(
                f"✓ Deleted {len(forecast_ids)} air quality forecast batches older than {days_to_keep} days"
            )
            
            return len(forecast_ids)
        
        except Exception as e:
            self._log_db_error("cleanup_old_forecasts", e)
            return 0
    
    def cleanup_old_forecast_data_points(self, hours_to_keep: int = 168) -> int:
        """
        Delete individual air quality data points older than X hours
        
        Args:
            hours_to_keep: Number of hours to keep (default: 168 = 7 days)
        
        Returns:
            Number of data points deleted
        
        Explanation:
        - More granular than cleanup_old_forecasts
        - Deletes only old valid_time data points
        - Useful if you want to keep forecast batches but not old data
        """
        
        try:
            delete_query = """
            DELETE FROM air_quality_data
            WHERE valid_time < DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            
            cursor = self.db.connection.cursor()
            cursor.execute(delete_query, (hours_to_keep,))
            deleted_count = cursor.rowcount
            self.db.connection.commit()
            cursor.close()
            
            self.logger.info(f"✓ Deleted {deleted_count} air quality data points older than {hours_to_keep} hours")
            
            return deleted_count
        
        except Exception as e:
            self._log_db_error("cleanup_old_forecast_data_points", e)
            return 0
        
        