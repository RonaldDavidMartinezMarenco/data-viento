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
from datetime import datetime


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
    
    
    def get_current_air_quality(self, location_id: int) -> Optional[Dict[str, Any]]:
        """
        Get current air quality for a location
        
        Args:
            location_id: Location ID
        
        Returns:
            Dictionary with current air quality data or None
        
        Example:
            >>> service = AirQualityService()
            >>> current = service.get_current_air_quality(location_id=1)
            >>> print(current['pm2_5'])
            12.5
        """
        
        query = """
        SELECT 
            aqc.air_quality_current_id,
            aqc.location_id,
            aqc.observation_time,
            aqc.pm2_5,
            aqc.pm10,
            aqc.european_aqi,
            aqc.us_aqi,
            aqc.nitrogen_dioxide,
            aqc.ozone,
            aqc.sulphur_dioxide,
            aqc.carbon_monoxide,
            aqc.dust,
            aqc.ammonia,
            aqc.updated_at
        FROM air_quality_current aqc
        WHERE aqc.location_id = %s
        ORDER BY aqc.observation_time DESC
        LIMIT 1
        """
        
        try:
            result = self.db.execute_query(query, (location_id,))
            
            if not result:
                self.logger.warning(f"No current air quality found for location {location_id}")
                return None
            
            row = result[0]
            
            return {
                "air_quality_current_id": row[0],
                "location_id": row[1],
                "observation_time": row[2].isoformat() if row[2] else None,
                "pm2_5": float(row[3]) if row[3] is not None else None,
                "pm10": float(row[4]) if row[4] is not None else None,
                "european_aqi": row[5],
                "us_aqi": row[6],
                "nitrogen_dioxide": float(row[7]) if row[7] is not None else None,
                "ozone": float(row[8]) if row[8] is not None else None,
                "sulphur_dioxide": float(row[9]) if row[9] is not None else None,
                "carbon_monoxide": float(row[10]) if row[10] is not None else None,
                "dust": float(row[11]) if row[11] is not None else None,
                "ammonia": float(row[12]) if row[12] is not None else None,
                "updated_at": row[13].isoformat() if row[13] else None,
            }
        
        except Exception as e:
            self._log_db_error("get_current_air_quality", e)
            return None


    def get_hourly_air_quality(
        self,
        location_id: int,
        hours: int = 24,
        parameters: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get hourly air quality forecast for a location
        
        Args:
            location_id: Location ID
            hours: Number of forecast hours (default: 24)
            parameters: List of parameter codes (default: all AQ params)
        
        Returns:
            Dictionary with hourly air quality data structured by parameter
        
        Example:
            >>> service = AirQualityService()
            >>> hourly = service.get_hourly_air_quality(
            ...     location_id=1,
            ...     hours=24,
            ...     parameters=['pm2_5', 'pm10', 'aqi_european']
            ... )
            >>> print(hourly['parameters']['pm2_5']['values'])
            [12.5, 13.2, 14.1, ...]
        """
        
        # Default parameters if none specified
        if parameters is None:
            parameters = [
                'pm2_5',
                'pm10',
                'aqi_european',
                'aqi_us',
                'no2',
                'o3',
                'so2',
                'co'
            ]
        
        try:
            # Step 1: Get the latest forecast batch for this location
            forecast_query = """
            SELECT air_quality_id, forecast_reference_time, model_id
            FROM air_quality_forecasts
            WHERE location_id = %s
            ORDER BY forecast_reference_time DESC
            LIMIT 1
            """
            
            forecast_result = self.db.execute_query(forecast_query, (location_id,))
            
            if not forecast_result:
                self.logger.warning(f"No air quality forecast batch found for location {location_id}")
                return None
            
            forecast_id = forecast_result[0][0]
            forecast_time = forecast_result[0][1]
            model_id = forecast_result[0][2]
            
            # Step 2: Get parameter IDs
            placeholders = ','.join(['%s'] * len(parameters))
            param_query = f"""
            SELECT parameter_id, parameter_code, parameter_name, unit
            FROM weather_parameters
            WHERE parameter_code IN ({placeholders})
                AND api_endpoint = 'air_quality'
            """
            
            param_results = self.db.execute_query(param_query, parameters)
            
            if not param_results:
                self.logger.warning(f"No parameters found for codes: {parameters}")
                return None
            
            # Map parameter_id to parameter_code
            param_map = {row[0]: row[1] for row in param_results}
            param_names = {row[0]: row[2] for row in param_results}
            param_units = {row[0]: row[3] for row in param_results}
            
            # Step 3: Get air quality data for all parameters
            param_ids = list(param_map.keys())
            param_placeholders = ','.join(['%s'] * len(param_ids))
            
            data_query = f"""
            SELECT 
                aqd.parameter_id,
                aqd.valid_time,
                aqd.value,
                aqd.unit,
                aqd.aqi_category,
                aqd.health_impact
            FROM air_quality_data aqd
            WHERE aqd.air_quality_id = %s
                AND aqd.parameter_id IN ({param_placeholders})
                AND aqd.valid_time >= NOW()
                AND aqd.valid_time < DATE_ADD(NOW(), INTERVAL %s HOUR)
            ORDER BY aqd.parameter_id, aqd.valid_time ASC
            """
            
            query_params = [forecast_id] + param_ids + [hours]
            data_results = self.db.execute_query(data_query, query_params)
            
            if not data_results:
                self.logger.warning(f"No air quality data found for forecast_id {forecast_id}")
                return None
            
            # Step 4: Structure data by parameter
            result = {
                "air_quality_id": forecast_id,
                "location_id": location_id,
                "model_id": model_id,
                "forecast_reference_time": forecast_time.isoformat() if forecast_time else None,
                "parameters": {}
            }
            
            # Group data by parameter_id
            for row in data_results:
                parameter_id = row[0]
                valid_time = row[1]
                value = row[2]
                unit = row[3]
                aqi_category = row[4]
                health_impact = row[5]
                
                param_code = param_map.get(parameter_id)
                
                if param_code not in result["parameters"]:
                    result["parameters"][param_code] = {
                        "name": param_names.get(parameter_id),
                        "unit": param_units.get(parameter_id),
                        "times": [],
                        "values": [],
                        "categories": [],
                        "health_impacts": []
                    }
                
                result["parameters"][param_code]["times"].append(
                    valid_time.isoformat() if valid_time else None
                )
                result["parameters"][param_code]["values"].append(
                    float(value) if value is not None else None
                )
                result["parameters"][param_code]["categories"].append(aqi_category)
                result["parameters"][param_code]["health_impacts"].append(health_impact)
            
            return result
        
        except Exception as e:
            self._log_db_error("get_hourly_air_quality", e)
            return None


    def get_all_air_quality_data(
        self,
        location_id: int,
        hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Get all air quality data for a location (current + hourly)
        
        This is the main method used by the /air-quality/all API endpoint
        
        Args:
            location_id: Location ID
            hours: Number of forecast hours (default: 24)
        
        Returns:
            Dictionary with all air quality data
        
        Example:
            >>> service = AirQualityService()
            >>> air_quality = service.get_all_air_quality_data(location_id=1)
            >>> print(air_quality['current']['pm2_5'])
            12.5
            >>> print(len(air_quality['hourly']['parameters']['pm2_5']['values']))
            24
        """
        
        try:
            result = {
                "success": True,
                "location_id": location_id,
                "current": None,
                "hourly": None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Fetch current air quality
            current = self.get_current_air_quality(location_id)
            if current:
                result["current"] = current
            
            # Fetch hourly forecast
            hourly = self.get_hourly_air_quality(location_id, hours=hours)
            if hourly:
                result["hourly"] = hourly
            
            # Check if we got any data
            if not current and not hourly:
                self.logger.warning(f"No air quality data found for location {location_id}")
                return None
            
            return result
        
        except Exception as e:
            self._log_db_error("get_all_air_quality_data", e)
            return None

    
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
        
        