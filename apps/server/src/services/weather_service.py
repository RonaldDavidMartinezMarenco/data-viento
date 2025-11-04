"""
Weather Service

Handles weather forecast operations:
1. Fetch weather data from Open-Meteo API
2. Parse responses using Pydantic models
3. Insert data into database (current_weather, weather_forecasts, forecast_data, weather_forecasts_daily)

Maps to tables:
- current_weather
- weather_forecasts
- forecast_data
- weather_forecasts_daily
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional, Dict, Any
from src.services.base_service import BaseService
from src.services.location_service import LocationService
from src.models.weather_models import ForecastResponse
from src.db.database import DatabaseConnection

class WeatherService (BaseService):
    """
    Service for weather forecast operations
    
    Workflow:
    1. Fetch data from Open-Meteo
    2. Parse with Pydantic models (validation)
    3. Get/create location
    4. Get/create weather model
    5. Insert current weather (if available)
    6. Insert hourly forecast (if available)
    7. Insert daily forecast (if available)
    """
    
    def __init__(self, db: Optional[DatabaseConnection] = None):
        """Initialize weather service"""
        super().__init__(db)
        self.location_service = LocationService(self.db)
        self.weather_model_id = self._get_or_create_weather_model()
        
    def _get_or_create_weather_model(self) -> int:
        """
        Get or create weather model for Open-Meteo forecasts
        
        Returns:
            model_id for OM_FORECAST
        
        Explanation:
        - Checks if OM_FORECAST model exists
        - If not, creates it with metadata
        - Returns model_id for use in all weather inserts
        """
        
        # Check if model exists
        query = "SELECT model_id FROM weather_models WHERE model_code = 'OM_FORECAST'"
        result = self.db.execute_query(query)
        
        if result:
            return result [0][0]
        
        # Create model if not exists
        query = """
        INSERT INTO weather_models (
            model_code, model_name, provider, provider_country,
            resolution_km, resolution_degrees, forecast_days, update_frequency_hours,
            temporal_resolution, geographic_coverage, model_type,
            is_active, description, created_at
        ) VALUES (
            'OM_FORECAST', 'Open-Meteo Forecast', 'Open-Meteo', 'Switzerland',
            11.0, 0.1, 16, 3, 'hourly', 'global', 'weather',
            TRUE, 'Open-Meteo weather forecast API (ICON, GFS, ECMWF)', NOW()
        )
        """

        model_id = self.db.execute_insert(query)
        self.logger.info(f"✓ Created weather model: OM_FORECAST (ID: {model_id})")
        return model_id

    async def fetch_and_save_weather(
        self,
        location_name: str,
        latitude: float,
        longitude: float,
        include_current: bool = True,
        include_hourly: bool = False,
        include_daily: bool = True,
        forecast_days: int = 5,
        **location_kwargs
    ) -> Dict[str, Any]:
        """
        Complete workflow: Fetch weather from API and save to database
        
        Args:
            location_name: Location name (e.g., "Madrid")
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            include_current: Fetch current weather
            include_hourly: Fetch hourly forecast
            include_daily: Fetch daily forecast
            forecast_days: Number of forecast days (1-16)
            **location_kwargs: Additional location fields (timezone, country, etc.)
        
        Returns:
            Dictionary with operation results
        
        Example:
            >>> weather_service = WeatherService()
            >>> result = await weather_service.fetch_and_save_weather(
            ...     "Madrid", 40.4168, -3.7038,
            ...     include_current=True,
            ...     include_daily=True,
            ...     timezone="Europe/Madrid"
            ... )
            >>> print(result)
            {
                'success': True,
                'location_id': 1,
                'current_saved': True,
                'daily_saved': True,
                'forecast_days': 7
            }
        """
        result = {
            'success': False,
            'location_id': None,
            'current_saved': False,
            'hourly_saved': False,
            'daily_saved': False,
            'error': None
        }
        try:
            self.logger.info(f"Fetching weather data for {location_name} ({latitude}, {longitude})")
        
            api_response = await self.api_client.get_weather_forecast(
                latitude=latitude,
                longitude=longitude,
                include_current=include_current,
                include_hourly=include_hourly,
                include_daily=include_daily,
                timezone=location_kwargs.get('timezone', 'auto'),
                forecast_days=forecast_days
            )
            
            if not api_response:
                result['error'] = 'Failed to fetch data from API'
                return result
            
            # Step 2: Parse response with Pydantic model (validates data)
            forecast = ForecastResponse(**api_response)
            self.logger.info(f"✓ API data validated successfully")
            
            # Step 3: Get or create location
            location_id = self.location_service.get_or_create_location(
                name = location_name,
                latitude=latitude,
                longitude=longitude,
                **location_kwargs
            )
            result ['location_id'] = location_id
            
            # Step 4: Save current weather (if available)
            if include_current and forecast.current:
                current_saved = self._save_current_weather(
                    location_id=location_id,
                    current_data=forecast.current
                )
                result ['current_saved'] = current_saved
                
            # Step 5: Save hourly forecast (if available)
            if include_hourly and forecast.hourly:
                hourly_saved = self._save_hourly_forecast(
                    location_id=location_id,
                    hourly_data=forecast.hourly,
                    forecast_metadata=forecast
                )
                result['hourly_saved'] = hourly_saved    
                
            # Step 6: Save daily forecast (if available)
            if include_daily and forecast.daily:
                daily_saved = self._save_daily_forecast(
                    location_id=location_id,
                    daily_data=forecast.daily
                )
                result['daily_saved'] = daily_saved
                result['forecast_days'] = len(forecast.daily.time)
                
            result['success'] = True
            self.logger.info(f"✓ Weather data saved successfully for {location_name}")
            
        except Exception as e:
            self.logger.error(f"✗ Error in fetch_and_save_weather: {e}")
            result['error'] = str(e)
            
        return result
    
    def _save_current_weather(
            self,
            location_id: int,
            current_data,
        ) -> bool:
            """
            Save current weather to database
            
            Maps to: current_weather table
            
            Args:
                location_id: Location ID
                current_data: CurrentWeatherData Pydantic model
            
            Returns:
                True if saved successfully
            
            Explanation:
            - Uses ON DUPLICATE KEY UPDATE to update existing row
            - Only one current weather record per location
            - Automatically updates if newer data arrives
            """
            
            query = """
            INSERT INTO current_weather (
                location_id, model_id, observation_time,
                temperature_2m, relative_humidity_2m, apparent_temperature,
                precipitation, weather_code, cloud_cover,
                wind_speed_10m, wind_direction_10m,
                created_at, updated_at
            ) VALUES (
                %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
            ON DUPLICATE KEY UPDATE
                model_id = VALUES(model_id),
                temperature_2m = VALUES(temperature_2m),
                relative_humidity_2m = VALUES(relative_humidity_2m),
                apparent_temperature = VALUES(apparent_temperature),
                precipitation = VALUES(precipitation),
                weather_code = VALUES(weather_code),
                cloud_cover = VALUES(cloud_cover),
                wind_speed_10m = VALUES(wind_speed_10m),
                wind_direction_10m = VALUES(wind_direction_10m),
                observation_time = NOW(),
                updated_at = NOW()
            """
            
            params = (
                location_id,
                self.weather_model_id,
                current_data.temperature_2m,
                current_data.relative_humidity_2m,
                current_data.apparent_temperature,
                current_data.precipitation,
                current_data.weather_code,
                current_data.cloud_cover,
                current_data.wind_speed_10m,
                current_data.wind_direction_10m,
            )
            
            try:
                self.db.execute_insert(query, params)
                self.logger.info(f"✓ Current weather saved for location {location_id}")
                return True
            except Exception as e:
                self._log_db_error("save_current_weather", e)
                return False
        
    def _save_daily_forecast(
        self,
        location_id: int,
        daily_data,
    ) -> bool:
        """
        Save daily forecast to database
        
        Maps to: weather_forecasts_daily table
        
        Args:
            location_id: Location ID
            daily_data: DailyWeatherData Pydantic model
        
        Returns:
            True if saved successfully
        
        Explanation:
        - Saves multiple days (each day is a separate row)
        - Uses bulk insert for efficiency
        - ON DUPLICATE KEY UPDATE for idempotency
        """
        
        if not daily_data.time:
            return False
        
        query = """
        INSERT INTO weather_forecasts_daily (
            location_id, model_id, valid_date,
            temperature_2m_max, temperature_2m_min,
            precipitation_sum, precipitation_hours, precipitation_probability_max,
            weather_code, sunrise, sunset, sunshine_duration,
            uv_index_max, wind_speed_10m_max, wind_gusts_10m_max,
            wind_direction_10m_dominant, forecast_reference_time,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
        )
        ON DUPLICATE KEY UPDATE 
            temperature_2m_max = VALUES(temperature_2m_max),
            temperature_2m_min = VALUES(temperature_2m_min),
            precipitation_sum = VALUES(precipitation_sum),
            precipitation_hours = VALUES(precipitation_hours),
            precipitation_probability_max = VALUES(precipitation_probability_max),
            weather_code = VALUES(weather_code),
            sunrise = VALUES(sunrise),
            sunset = VALUES(sunset),
            sunshine_duration = VALUES(sunshine_duration),
            uv_index_max = VALUES(uv_index_max),
            wind_speed_10m_max = VALUES(wind_speed_10m_max),
            wind_gusts_10m_max = VALUES(wind_gusts_10m_max),
            wind_direction_10m_dominant = VALUES(wind_direction_10m_dominant),
            forecast_reference_time = NOW(),   
            updated_at = NOW()
        """
        
        # Prepare bulk data
        rows = []
        for i, date in enumerate(daily_data.time):
            row = (
                location_id,
                self.weather_model_id,
                date,  # valid_date
                daily_data.temperature_2m_max[i] if daily_data.temperature_2m_max else None,
                daily_data.temperature_2m_min[i] if daily_data.temperature_2m_min else None,
                daily_data.precipitation_sum[i] if daily_data.precipitation_sum else None,
                daily_data.precipitation_hours[i] if daily_data.precipitation_hours else None,
                daily_data.precipitation_probability_max[i] if daily_data.precipitation_probability_max else None,
                daily_data.weather_code[i] if daily_data.weather_code else None,
                daily_data.sunrise[i] if daily_data.sunrise else None,
                daily_data.sunset[i] if daily_data.sunset else None,
                daily_data.sunshine_duration[i] if daily_data.sunshine_duration else None,
                daily_data.uv_index_max[i] if daily_data.uv_index_max else None,
                daily_data.wind_speed_10m_max[i] if daily_data.wind_speed_10m_max else None,
                daily_data.wind_gusts_10m_max[i] if daily_data.wind_gusts_10m_max else None,
                daily_data.wind_direction_10m_dominant[i] if daily_data.wind_direction_10m_dominant else None,
            )
            rows.append(row)
        
        try:
            rows_inserted = self.db.execute_bulk_insert(query, rows)
            self.logger.info(f"✓ Daily forecast saved: {rows_inserted} days for location {location_id}")
            return True
        except Exception as e:
            self._log_db_error("save_daily_forecast", e)
            return False
    
    # ...existing code...

    def _save_hourly_forecast(
        self,
        location_id: int,
        hourly_data,
        forecast_metadata
    ) -> bool:
        """
        Save hourly forecast to database
        
        Maps to: weather_forecasts + forecast_data tables
        
        Workflow:
        1. Create forecast batch record (weather_forecasts table)
        2. For each parameter in hourly data:
        a. Get or create parameter_id from weather_parameters
        b. Insert all hourly values into forecast_data
        
        Args:
            location_id: Location ID
            hourly_data: HourlyWeatherData Pydantic model
            forecast_metadata: ForecastResponse Pydantic model (contains timezone, etc.)
        
        Returns:
            True if saved successfully
        
        Explanation:
        - Creates ONE forecast batch
        - Inserts MULTIPLE parameters (temperature, humidity, wind, etc.)
        - Each parameter has MULTIPLE time points (hourly values)
        - Uses forecast_data.value column for all numeric values
        """
        
        if not hourly_data.time:
            self.logger.warning("No hourly data to save")
            return False
        
        try:
            # Step 1: Create forecast batch record
            forecast_query = """
            INSERT INTO weather_forecasts (
                location_id, model_id, forecast_reference_time,
                generation_time_ms, timezone, utc_offset_seconds,
                created_at
            ) VALUES (
                %s, %s, NOW(), %s, %s, %s, NOW()
            )
            """
            
            forecast_params = (
                location_id,
                self.weather_model_id,
                forecast_metadata.generationtime_ms,
                forecast_metadata.timezone,
                forecast_metadata.utc_offset_seconds,
            )
            
            forecast_id = self.db.execute_insert(forecast_query, forecast_params)
            
            if forecast_id <= 0:
                self.logger.error("Failed to create forecast batch")
                return False
            
            self.logger.info(f"✓ Created forecast batch ID: {forecast_id}")
            
            # Step 2: Prepare parameter mapping
            # This maps Open-Meteo field names to our parameter codes
            parameter_mapping = {
                'temperature_2m': 'temp_2m',
                'relative_humidity_2m': 'humidity_2m',
                'precipitation_probability': 'precip_prob',
                'precipitation': 'precip',
                'weather_code': 'weather_code',
                'wind_speed_10m': 'wind_speed_10m',
                'wind_direction_10m': 'wind_dir_10m',
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
        """
        Insert all hourly values for a single parameter
        
        Args:
            forecast_id: Forecast batch ID
            parameter_id: Parameter ID
            time_array: Array of timestamps (from hourly_data.time)
            value_array: Array of values (from hourly_data.temperature_2m, etc.)
            param_code: Parameter code (for determining unit)
        
        Returns:
            Number of rows inserted
        
        Explanation:
        - Bulk inserts all hourly values for one parameter
        - Calculates forecast_hour (hours from now)
        - Uses INSERT IGNORE to avoid duplicates
        """
        
        # Get unit from weather_parameters
        unit_query = "SELECT unit FROM weather_parameters WHERE parameter_id = %s"
        unit_result = self.db.execute_query(unit_query, (parameter_id,))
        unit = unit_result[0][0] if unit_result else None
        
        # Prepare bulk insert
        insert_query = """
        INSERT IGNORE INTO forecast_data (
            forecast_id, parameter_id, valid_time, forecast_hour,
            value, text_value, unit, confidence_score, quality_flag
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        rows = []
        for i, timestamp in enumerate(time_array):
            # Calculate forecast_hour (index = hours from now)
            forecast_hour = i
            
            # Get value (could be None)
            value = value_array[i] if i < len(value_array) else None
            
            row = (
                forecast_id,
                parameter_id,
                timestamp,          # valid_time
                forecast_hour,
                value,              # value
                None,               # text_value
                unit,               # unit
                None,               # confidence_score (not provided by Open-Meteo)
                'good',             # quality_flag
            )
            rows.append(row)
        
        # Execute bulk insert
        rows_inserted = self.db.execute_bulk_insert(insert_query, rows)
        
        return rows_inserted
    
    def cleanup_old_forecasts(self, days_to_keep: int = 5) -> int:
        """
        Delete old forecast batches and their data
        
        Args:
            days_to_keep: Number of days to keep (default: 7)
        
        Returns:
            Number of forecast batches deleted
        
        Explanation:
        - Deletes forecast batches older than X days
        - Cascade deletes forecast_data rows (if FK constraint set)
        - Keeps database size manageable
        - Run this daily via cron job
        
        Example:
            >>> service = WeatherService()
            >>> deleted = service.cleanup_old_forecasts(days_to_keep=7)
            >>> print(f"Deleted {deleted} old forecast batches")
        """
    
        try:
            # Step 1: Find old forecast IDs
            select_query = """
            SELECT forecast_id, location_id, forecast_reference_time
            FROM weather_forecasts
            WHERE forecast_reference_time < DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            
            old_forecasts = self.db.execute_query(select_query, (days_to_keep,))
            
            if not old_forecasts:
                self.logger.info(f"No forecasts older than {days_to_keep} days to delete")
                return 0
            
            forecast_ids = [row[0] for row in old_forecasts]
            
            # Step 2: Delete forecast_data rows (if no CASCADE)
            if forecast_ids:
                placeholders = ','.join(['%s'] * len(forecast_ids))
                delete_data_query = f"""
                DELETE FROM forecast_data
                WHERE forecast_id IN ({placeholders})
                """
                
                self.db.execute_query(delete_data_query, forecast_ids)
                self.logger.info(f"✓ Deleted forecast_data for {len(forecast_ids)} batches")
            
            # Step 3: Delete forecast batches
            delete_forecast_query = f"""
            DELETE FROM weather_forecasts
            WHERE forecast_id IN ({placeholders})
            """
            
            self.db.execute_query(delete_forecast_query, forecast_ids)
            
            self.logger.info(
                f"✓ Deleted {len(forecast_ids)} forecast batches older than {days_to_keep} days"
            )
            
            return len(forecast_ids)
        
        except Exception as e:
            self._log_db_error("cleanup_old_forecasts", e)
            return 0


    def cleanup_old_forecast_data_points(self, hours_to_keep: int = 168) -> int:
        """
        Delete individual forecast data points older than X hours
        
        Args:
            hours_to_keep: Number of hours to keep (default: 168 = 7 days)
        
        Returns:
            Number of data points deleted
        
        Explanation:
        - More granular than cleanup_old_forecasts
        - Deletes only old valid_time data points
        - Useful if you want to keep forecast batches but not old data
        
        Example:
            >>> service = WeatherService()
            >>> deleted = service.cleanup_old_forecast_data_points(hours_to_keep=168)
            >>> print(f"Deleted {deleted} old data points")
        """
        
        try:
            delete_query = """
            DELETE FROM forecast_data
            WHERE valid_time < DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            
            # Execute with affected rows count
            cursor = self.db.connection.cursor()
            cursor.execute(delete_query, (hours_to_keep,))
            deleted_count = cursor.rowcount
            self.db.connection.commit()
            cursor.close()
            
            self.logger.info(f"✓ Deleted {deleted_count} forecast data points older than {hours_to_keep} hours")
            
            return deleted_count
        
        except Exception as e:
            self._log_db_error("cleanup_old_forecast_data_points", e)
            return 0
        
 