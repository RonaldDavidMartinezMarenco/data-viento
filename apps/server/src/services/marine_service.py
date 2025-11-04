"""
Marine Service

Handles marine weather operations:
1. Fetch marine data from Open-Meteo Marine API
2. Parse responses using Pydantic models
3. Insert data into database (marine_current, marine_forecasts, marine_data, marine_forecasts_daily)

Maps to tables (from schema.txt):
- marine_current (stores latest marine conditions per location)
- marine_forecasts (metadata for hourly forecast batches)
- marine_data (individual hourly forecast data points)
- marine_forecasts_daily (daily marine forecast aggregates)

API Endpoint: https://marine-api.open-meteo.com/v1/marine
Documentation: https://open-meteo.com/en/docs/marine-weather-api
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional, Dict, Any
from src.services.base_service import BaseService
from src.services.location_service import LocationService
from src.models.marine_models import MarineResponse
from src.db.database import DatabaseConnection

class MarineService(BaseService):
    """
    Service for marine weather operations
    
    Workflow:
    1. Fetch data from Open-Meteo Marine API
    2. Parse with Pydantic models (validation)
    3. Get/create location
    4. Get/create marine model
    5. Insert current marine conditions (if available)
    6. Insert hourly forecast (if available)
    7. Insert daily forecast (if available)
    """
    def __init__(self, db = None):
        super().__init__(db)
        self.location_service = LocationService(self.db)
        self.marine_model_id = self._get_or_create_marine_model()
        
        
    def _get_or_create_marine_model(self) -> int:
        """
        Get or create marine model for Open-Meteo Marine forecasts
        
        Returns:
            model_id for OM_MARINE
        
        Explanation:
        - Checks if OM_MARINE model exists
        - If not, creates it with metadata
        - Returns model_id for use in all marine inserts
        """
        
        # Check if model exists
        query = "SELECT model_id FROM weather_models WHERE model_code = 'ECMWF_WAVES'"
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
            'OM_MARINE', 'Open-Meteo Marine', 'Open-Meteo', 'Switzerland',
            5.0, 0.05, 7, 6, 'hourly', 'global', 'marine',
            TRUE, 'Open-Meteo marine weather forecast (waves, ocean currents, sea temperature)', NOW()
        )
        """
        
        model_id = self.db.execute_insert(query)
        self.logger.info(f"✓ Created marine model: OM_MARINE (ID: {model_id})")
        return model_id
    
    async def fetch_and_save_marine(
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
        Complete workflow: Fetch marine data from API and save to database
        
        Args:
            location_name: Location name (e.g., "Barcelona Coast")
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            include_current: Fetch current marine conditions
            include_hourly: Fetch hourly forecast
            include_daily: Fetch daily forecast
            forecast_days: Number of forecast days (1-7)
            **location_kwargs: Additional location fields (timezone, country, etc.)
        
        Returns:
            Dictionary with operation results
        
        Example:
            >>> marine_service = MarineService()
            >>> result = await marine_service.fetch_and_save_marine(
            ...     "Barcelona Coast", 41.3851, 2.1734,
            ...     include_current=True,
            ...     include_daily=True,
            ...     timezone="Europe/Madrid"
            ... )
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
            self.logger.info(f"Fetching marine data for {location_name} ({latitude}, {longitude})")
            
            # Step 1: Fetch data from API
            api_response = await self.api_client.get_marine_forecast(
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
            marine_response = MarineResponse(**api_response)
            self.logger.info(f"✓ API data validated successfully")
            
            # Step 3: Get or create location
            location_id = self.location_service.get_or_create_location(
                name=location_name,
                latitude=latitude,
                longitude=longitude,
                **location_kwargs
            )
            
            result['location_id'] = location_id
            
            # Step 4: Save current marine conditions (if available)
            if include_current and marine_response.current:
                current_saved = self._save_current_marine(
                    location_id=location_id,
                    current_data=marine_response.current
                )
                result['current_saved'] = current_saved
            
            # Step 5: Save hourly forecast (if available)
            if include_hourly and marine_response.hourly:
                hourly_saved = self._save_hourly_forecast(
                    location_id=location_id,
                    hourly_data=marine_response.hourly,
                    marine_metadata=marine_response
                )
                result['hourly_saved'] = hourly_saved
            
            # Step 6: Save daily forecast (if available)
            if include_daily and marine_response.daily:
                daily_saved = self._save_daily_forecast(
                    location_id=location_id,
                    daily_data=marine_response.daily
                )
                result['daily_saved'] = daily_saved
                result['forecast_days'] = len(marine_response.daily.time)
            
            result['success'] = True
            self.logger.info(f"✓ Marine data saved successfully for {location_name}")
        
        except Exception as e:
            self.logger.error(f"✗ Error in fetch_and_save_marine: {e}", exc_info=True)
            result['error'] = str(e)
        
        return result    
    
    
    def _save_current_marine(
        self,
        location_id: int,
        current_data
    ) -> bool:
        """
        Save current marine conditions to database
        
        Schema mapping (marine_current):
        - marine_current_id (PK, AUTO_INCREMENT)
        - location_id (FK to locations, UNIQUE)
        - observation_time (TIMESTAMP)
        - wave_height, wave_direction, wave_period (wave parameters)
        - swell_wave_* (swell wave parameters)
        - wind_wave_height (wind wave parameters)
        - sea_surface_temperature (water temperature)
        - ocean_current_velocity, ocean_current_direction (current parameters)
        - updated_at (TIMESTAMP)
        
        Args:
            location_id: Location ID
            current_data: MarineCurrent Pydantic model
        
        Returns:
            True if saved successfully
        
        Explanation:
        - Uses ON DUPLICATE KEY UPDATE to update existing row
        - Only one current marine record per location
        - Automatically updates if newer data arrives
        """
        
        query = """
        INSERT INTO marine_current (
            location_id, observation_time,
            wave_height, wave_direction, wave_period,
            swell_wave_height, swell_wave_direction, swell_wave_period,
            wind_wave_height, sea_surface_temperature,
            ocean_current_velocity, ocean_current_direction,
            updated_at
        ) VALUES (
            %s, NOW(),
            %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            NOW()
        )
        ON DUPLICATE KEY UPDATE
            observation_time = NOW(),
            wave_height = VALUES(wave_height),
            wave_direction = VALUES(wave_direction),
            wave_period = VALUES(wave_period),
            swell_wave_height = VALUES(swell_wave_height),
            swell_wave_direction = VALUES(swell_wave_direction),
            swell_wave_period = VALUES(swell_wave_period),
            wind_wave_height = VALUES(wind_wave_height),
            sea_surface_temperature = VALUES(sea_surface_temperature),
            ocean_current_velocity = VALUES(ocean_current_velocity),
            ocean_current_direction = VALUES(ocean_current_direction),
            updated_at = NOW()
        """
        
        params = (
            location_id,
            current_data.wave_height,
            current_data.wave_direction,
            current_data.wave_period,
            current_data.swell_wave_height,
            current_data.swell_wave_direction,
            current_data.swell_wave_period,
            current_data.wind_wave_height,
            current_data.sea_surface_temperature,
            current_data.ocean_current_velocity,
            current_data.ocean_current_direction,
        )
        
        try:
            self.db.execute_insert(query, params)
            self.logger.info(f"✓ Current marine conditions saved for location {location_id}")
            return True
        except Exception as e:
            self._log_db_error("save_current_marine", e)
            return False
    
    def _save_daily_forecast(
        self,
        location_id: int,
        daily_data
    ) -> bool:
        """
        Save daily marine forecast to database
        
        Schema mapping (marine_forecasts_daily):
        - forecast_day_id (PK, AUTO_INCREMENT)
        - location_id (FK to locations)
        - model_id (FK to weather_models)
        - valid_date (DATE)
        - wave_height_max, wave_direction_dominant, wave_period_max
        - swell_wave_height_max, swell_wave_direction_dominant
        - sea_surface_temperature_mean
        - ocean_current_velocity_max
        - forecast_reference_time (TIMESTAMP)
        - created_at (TIMESTAMP)
        - UNIQUE KEY: (location_id, model_id, valid_date)
        
        Args:
            location_id: Location ID
            daily_data: MarineDaily Pydantic model
        
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
        INSERT INTO marine_forecasts_daily (
            location_id, model_id, valid_date,
            wave_height_max, wave_direction_dominant, wave_period_max,
            swell_wave_height_max, swell_wave_direction_dominant,
            forecast_reference_time, created_at,wind_wave_height_max
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s
        )
        ON DUPLICATE KEY UPDATE
            wave_height_max = VALUES(wave_height_max),
            wave_direction_dominant = VALUES(wave_direction_dominant),
            wave_period_max = VALUES(wave_period_max),
            swell_wave_height_max = VALUES(swell_wave_height_max),
            swell_wave_direction_dominant = VALUES(swell_wave_direction_dominant),
            forecast_reference_time = NOW(),
            wind_wave_height_max = VALUES(wind_wave_height_max)
        """
        
        # Prepare bulk data
        rows = []
        for i, date in enumerate(daily_data.time):
            row = (
                location_id,
                self.marine_model_id,
                date,  # valid_date
                daily_data.wave_height_max[i] if daily_data.wave_height_max else None,
                daily_data.wave_direction_dominant[i] if daily_data.wave_direction_dominant else None,
                daily_data.wave_period_max[i] if daily_data.wave_period_max else None,
                daily_data.swell_wave_height_max[i] if daily_data.swell_wave_height_max else None,
                daily_data.swell_wave_direction_dominant[i] if daily_data.swell_wave_direction_dominant else None,
                daily_data.wind_wave_height_max[i] if daily_data.wind_wave_height_max else None,
            )
            rows.append(row)
        
        try:
            rows_inserted = self.db.execute_bulk_insert(query, rows)
            self.logger.info(f"✓ Daily marine forecast saved: {rows_inserted} days for location {location_id}")
            return True
        except Exception as e:
            self._log_db_error("save_daily_forecast", e)
            return False
    
    def _save_hourly_forecast(
        self,
        location_id: int,
        hourly_data,
        marine_metadata
    ) -> bool:
        """
        Save hourly marine forecast to database
        
        Schema mapping:
        1. marine_forecasts (forecast batch metadata)
           - marine_id (PK, AUTO_INCREMENT)
           - location_id (FK)
           - model_id (FK)
           - forecast_reference_time (TIMESTAMP)
           - data_resolution (ENUM: 'hourly', '3hourly', 'daily')
           - generation_time_ms (DECIMAL)
           - timezone (VARCHAR)
           - utc_offset_seconds (INTEGER)
           - created_at (TIMESTAMP)
        
        2. marine_data (hourly data points)
           - data_id (PK, AUTO_INCREMENT)
           - marine_id (FK to marine_forecasts)
           - parameter_id (FK to weather_parameters)
           - valid_time (TIMESTAMP)
           - value (DECIMAL)
           - unit (VARCHAR)
           - wave_component (ENUM - optional)
           - sea_condition (ENUM - optional)
           - quality_flag (ENUM: 'good', 'fair', 'poor', 'missing')
           - UNIQUE KEY: (marine_id, parameter_id, valid_time)
        
        Args:
            location_id: Location ID
            hourly_data: MarineHourly Pydantic model
            marine_metadata: MarineResponse Pydantic model
        
        Returns:
            True if saved successfully
        """
        
        if not hourly_data.time:
            self.logger.warning("No hourly data to save")
            return False
        
        try:
            # Step 1: Create forecast batch record
            forecast_query = """
            INSERT INTO marine_forecasts (
                location_id, model_id, forecast_reference_time,
                generation_time_ms, timezone, utc_offset_seconds,
                created_at
            ) VALUES (
                %s, %s, NOW(), %s, %s, %s, NOW()
            )
            """
            
            forecast_params = (
                location_id,
                self.marine_model_id,
                marine_metadata.generationtime_ms,
                marine_metadata.timezone,
                marine_metadata.utc_offset_seconds,
            )
            
            forecast_id = self.db.execute_insert(forecast_query, forecast_params)
            
            if forecast_id <= 0:
                self.logger.error("Failed to create forecast batch")
                return False
            
            self.logger.info(f"✓ Created marine forecast batch ID: {forecast_id}")
            
            # Step 2: Prepare parameter mapping
            # Maps API field names to parameter codes
            parameter_mapping = {
                'wave_height': 'wave_height',
                'wave_direction': 'wave_direction',
                'wave_period': 'wave_period',
                'swell_wave_height': 'swell_wave_height',
                'swell_wave_direction': 'swell_wave_direction',
                'swell_wave_period': 'swell_wave_period',
                'wind_wave_height': 'wind_wave_height',
                'sea_surface_temperature': 'sea_temp',
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
                f"✓ Hourly marine forecast saved: {total_rows} data points "
                f"({len(hourly_data.time)} hours x {len(parameter_mapping)} parameters)"
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
        
        Schema mapping (marine_data):
        - data_id: AUTO_INCREMENT PRIMARY KEY
        - marine_id: FK to marine_forecasts
        - parameter_id: FK to weather_parameters
        - valid_time: TIMESTAMP
        - value: DECIMAL(12,6)
        - unit: VARCHAR(20)
        - wave_component: ENUM (optional - set to NULL)
        - sea_condition: ENUM (optional - set to NULL)
        - quality_flag: ENUM DEFAULT 'good'
        
        Args:
            forecast_id: Forecast batch ID (marine_id)
            parameter_id: Parameter ID
            time_array: Array of timestamps
            value_array: Array of values
            param_code: Parameter code
        
        Returns:
            Number of rows inserted
        """
        
        # Get unit from weather_parameters
        unit_query = "SELECT unit FROM weather_parameters WHERE parameter_id = %s"
        unit_result = self.db.execute_query(unit_query, (parameter_id,))
        unit = unit_result[0][0] if unit_result else None
        
        # Prepare bulk insert
        insert_query = """
        INSERT IGNORE INTO marine_data (
            marine_id, parameter_id, valid_time,
            value, unit, quality_flag
        ) VALUES (
            %s, %s, %s, %s, %s, 'good'
        )
        """
        
        rows = []
        for i, timestamp in enumerate(time_array):
            # Get value (could be None)
            value = value_array[i] if i < len(value_array) else None
            
            if value is not None:  # Only insert non-null values
                row = (
                    forecast_id,      # marine_id (FK)
                    parameter_id,     # parameter_id (FK)
                    timestamp,        # valid_time
                    value,            # value
                    unit,             # unit
                    # quality_flag = 'good' (in VALUES clause)
                    # wave_component = NULL (default)
                    # sea_condition = NULL (default)
                )
                rows.append(row)
        
        if not rows:
            return 0
        
        # Execute bulk insert
        rows_inserted = self.db.execute_bulk_insert(insert_query, rows)
        
        return rows_inserted
    
    # ==================== CLEANUP METHODS ====================
    
    def cleanup_old_forecasts(self, days_to_keep: int = 7) -> int:
        """
        Delete old marine forecast batches and their data
        
        Args:
            days_to_keep: Number of days to keep (default: 7)
        
        Returns:
            Number of forecast batches deleted
        
        Explanation:
        - Deletes forecast batches older than X days
        - Cascade deletes marine_data rows
        - Keeps database size manageable
        - Run this daily via cron job
        """
        
        try:
            # Step 1: Find old forecast IDs
            select_query = """
            SELECT marine_id, location_id, forecast_reference_time
            FROM marine_forecasts
            WHERE forecast_reference_time < DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            
            old_forecasts = self.db.execute_query(select_query, (days_to_keep,))
            
            if not old_forecasts:
                self.logger.info(f"No marine forecasts older than {days_to_keep} days to delete")
                return 0
            
            forecast_ids = [row[0] for row in old_forecasts]
            
            # Step 2: Delete marine_data rows (must delete before parent due to FK)
            if forecast_ids:
                placeholders = ','.join(['%s'] * len(forecast_ids))
                delete_data_query = f"""
                DELETE FROM marine_data
                WHERE marine_id IN ({placeholders})
                """
                
                self.db.execute_query(delete_data_query, forecast_ids)
                self.logger.info(f"✓ Deleted marine_data for {len(forecast_ids)} batches")
            
            # Step 3: Delete forecast batches
            delete_forecast_query = f"""
            DELETE FROM marine_forecasts
            WHERE marine_id IN ({placeholders})
            """
            
            self.db.execute_query(delete_forecast_query, forecast_ids)
            
            self.logger.info(
                f"✓ Deleted {len(forecast_ids)} marine forecast batches older than {days_to_keep} days"
            )
            
            return len(forecast_ids)
        
        except Exception as e:
            self._log_db_error("cleanup_old_forecasts", e)
            return 0
    
    def cleanup_old_forecast_data_points(self, hours_to_keep: int = 168) -> int:
        """
        Delete individual marine data points older than X hours
        
        Args:
            hours_to_keep: Number of hours to keep (default: 168 = 7 days)
        
        Returns:
            Number of data points deleted
        """
        
        try:
            delete_query = """
            DELETE FROM marine_data
            WHERE valid_time < DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            
            cursor = self.db.connection.cursor()
            cursor.execute(delete_query, (hours_to_keep,))
            deleted_count = cursor.rowcount
            self.db.connection.commit()
            cursor.close()
            
            self.logger.info(f"✓ Deleted {deleted_count} marine data points older than {hours_to_keep} hours")
            
            return deleted_count
        
        except Exception as e:
            self._log_db_error("cleanup_old_forecast_data_points", e)
            return 0
    