"""
Satellite Radiation Service

Handles satellite radiation data operations:
1. Fetch satellite radiation data from Open-Meteo Satellite API
2. Parse responses using Pydantic models
3. Process data: Calculate mean values (handling NULLs)
4. Insert processed data into database (satellite_radiation_data)

Maps to table:
- satellite_radiation_data (stores processed satellite radiation readings per location)

API Endpoint: https://customer-archive-api.open-meteo.com/v1/archive
Documentation: https://open-meteo.com/en/docs/satellite-api

Note: This service processes hourly data into aggregated statistics
"""


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional, Dict, Any, List
from statistics import mean
from src.services.base_service import BaseService
from src.services.location_service import LocationService
from src.models.satellite_models import SatelliteResponse
from src.db.database import DatabaseConnection
from datetime import datetime


class SatelliteService(BaseService):
    """
    Service for satellite radiation operations
    
    Workflow:
    1. Fetch hourly satellite data from Open-Meteo API
    2. Parse with Pydantic models (validation)
    3. Process data: Calculate mean values (skip NULLs)
    4. Get/create location
    5. Get/create satellite model
    6. Insert processed radiation data into database
    
    Special Features:
    - Calculates mean of hourly values
    - Handles NULL/None values gracefully
    - Stores aggregated statistics instead of raw hourly data
    """
    
    def __init__(self, db: Optional[DatabaseConnection] = None):
        """Initialize satellite service"""
        super().__init__(db)
        self.location_service = LocationService(self.db)
        self.satellite_model_id = self._get_or_create_satellite_model()
        
        
    def _get_or_create_satellite_model(self) -> int:
        """
        Get or create satellite model for Open-Meteo Satellite data
        
        Returns:
            model_id for OM_SATELLITE
        
        Explanation:
        - Checks if OM_SATELLITE model exists
        - If not, creates it with metadata
        - Returns model_id for use in all satellite inserts
        """
        
        # Check if model exists
        query = "SELECT model_id FROM weather_models WHERE model_code = 'CAMS_SOLAR'"
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
            'OM_SATELLITE', 'Open-Meteo Satellite', 'Open-Meteo', 'Switzerland',
            4.0, 0.04, 0, 24, 'hourly', 'global', 'satellite',
            TRUE, 'Open-Meteo satellite radiation data (CAMS, MSG)', NOW()
        )
        """
        
        model_id = self.db.execute_insert(query)
        self.logger.info(f"✓ Created satellite model: OM_SATELLITE (ID: {model_id})")
        return model_id
    
    
    async def fetch_and_save_satellite_data(
        self,
        location_name: str,
        latitude: float,
        longitude: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **location_kwargs
    ) -> Dict[str, Any]:
        """
        Complete workflow: Fetch satellite data from API, process, and save to database
        
        Args:
            location_name: Location name (e.g., "Madrid Solar Farm")
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            start_date: Start date (YYYY-MM-DD) - defaults to today
            end_date: End date (YYYY-MM-DD) - defaults to today
            **location_kwargs: Additional location fields (timezone, country, etc.)
        
        Returns:
            Dictionary with operation results
        
        Processing:
            1. Fetch hourly data for date range
            2. Calculate mean of each radiation parameter
            3. Skip NULL values in mean calculation
            4. Save aggregated statistics to database
        
        Example:
            >>> satellite_service = SatelliteService()
            >>> result = await satellite_service.fetch_and_save_satellite_data(
            ...     "Madrid Solar Farm",
            ...     40.4168,
            ...     -3.7038,
            ...     start_date="2024-01-01",
            ...     end_date="2024-01-31",
            ...     timezone="Europe/Madrid"
            ... )
        """
        
        result = {
            'success': False,
            'location_id': None,
            'data_saved': False,
            'processed_records': 0,
            'error': None
        }
        
        try:
            self.logger.info(f"Fetching satellite data for {location_name} ({latitude}, {longitude})")
            
            # Step 1: Fetch data from API
            api_response = await self.api_client.get_solar_radiation(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                timezone=location_kwargs.get('timezone', 'auto')
            )
            
            if not api_response:
                result['error'] = 'Failed to fetch data from API'
                return result
            
            # Step 2: Parse response with Pydantic model (validates data)
            satellite_response = SatelliteResponse(**api_response)
            self.logger.info(f"✓ API data validated successfully")
            
            if not satellite_response.hourly:
                result['error'] = 'No hourly data available'
                return result
            
            # Step 3: Get or create location
            location_id = self.location_service.get_or_create_location(
                name=location_name,
                latitude=latitude,
                longitude=longitude,
                **location_kwargs
            )
            result['location_id'] = location_id
            
            # Step 4: Process data - Calculate means (handling NULLs)
            processed_data = self._process_satellite_data(satellite_response.hourly)
            
            if not processed_data:
                result['error'] = 'No valid data after processing'
                return result
            
            # Step 5: Save processed data to database
            data_saved = self._save_satellite_data(
                location_id=location_id,
                processed_data=processed_data,
                start_date=start_date,
                end_date=end_date,
                tilt=0,
                azimuth=0
            )
            
            result['data_saved'] = data_saved
            result['processed_records'] = len(processed_data.get('timestamps', []))
            result['success'] = True
            
            self.logger.info(
                f"✓ Satellite data saved successfully for {location_name} "
                f"({result['processed_records']} records)"
            )
        
        except Exception as e:
            self.logger.error(f"✗ Error in fetch_and_save_satellite_data: {e}", exc_info=True)
            result['error'] = str(e)
        
        return result
    
    def _process_satellite_data(self, hourly_data) -> Dict[str, Any]:
        """
        Process hourly satellite data: Calculate means while handling NULL values
        
        Args:
            hourly_data: SatelliteRadiation Pydantic model
        
        Returns:
            Dictionary with processed statistics
        
        Processing Logic:
            - For each timestamp, calculate mean across all radiation parameters
            - Skip NULL/None values when calculating mean
            - If all values are NULL for a parameter, set result to NULL
            - Keep individual parameter means for detailed analysis
        
        Example Output:
            {
                'timestamps': ['2024-01-01 00:00', '2024-01-01 01:00', ...],
                'shortwave_radiation_mean': 245.5,
                'direct_radiation_mean': 180.2,
                'diffuse_radiation_mean': 65.3,
                'dni_mean': 210.8,
                'gti_mean': 250.1,
                'terrestrial_radiation_mean': 380.0,
                'total_records': 24,
                'valid_records': 23
            }
        """
        
        if not hourly_data.time:
            return {}
        
        # Define parameters to process
        radiation_params = {
            'shortwave_radiation': 'shortwave_radiation_mean',
            'direct_radiation': 'direct_radiation_mean',
            'diffuse_radiation': 'diffuse_radiation_mean',
            'direct_normal_irradiance': 'dni_mean',
            'global_tilted_irradiance': 'gti_mean',
            'terrestrial_radiation': 'terrestrial_radiation_mean'
        }
        
        processed = {
            'timestamps': hourly_data.time,
            'total_records': len(hourly_data.time),
            'valid_records': 0
        }
        
        # Process each radiation parameter
        for api_field, result_key in radiation_params.items():
            data_array = getattr(hourly_data, api_field, None)
            
            if data_array is None:
                processed[result_key] = None
                continue
            
            # Calculate mean, skipping NULL values
            mean_value = self._calculate_mean_skip_nulls(data_array)
            processed[result_key] = mean_value
            
            self.logger.debug(
                f"Processed {api_field}: {len(data_array)} values → mean = {mean_value}"
            )
        
        # Count valid records (timestamps with at least one non-NULL value)
        valid_count = 0
        for i in range(len(hourly_data.time)):
            has_value = any(
                getattr(hourly_data, param, None) and 
                i < len(getattr(hourly_data, param, [])) and
                getattr(hourly_data, param)[i] is not None
                for param in radiation_params.keys()
            )
            if has_value:
                valid_count += 1
        
        processed['valid_records'] = valid_count
        
        return processed
    
    
    def _calculate_mean_skip_nulls(self, values: List[Optional[float]]) -> Optional[float]:
        """
        Calculate mean of a list, skipping NULL/None values
        
        Args:
            values: List of float values (can contain None)
        
        Returns:
            Mean value, or None if all values are NULL
        
        Examples:
            >>> self._calculate_mean_skip_nulls([1.0, 2.0, 3.0])
            2.0
            >>> self._calculate_mean_skip_nulls([1.0, None, 3.0])
            2.0
            >>> self._calculate_mean_skip_nulls([None, None, None])
            None
            >>> self._calculate_mean_skip_nulls([])
            None
        """
        
        # Filter out None values
        valid_values = [v for v in values if v is not None]
        
        if not valid_values:
            return None
        
        try:
            return round(mean(valid_values), 2)
        except Exception as e:
            self.logger.warning(f"Error calculating mean: {e}")
            return None
        
        
    def _save_satellite_data(
        self,
        location_id: int,
        processed_data: Dict[str, Any],
        start_date: Optional[str],
        end_date: Optional[str],
        tilt: int,
        azimuth: int
    ) -> bool:
        """
        Save processed satellite radiation data to database
        
        Schema mapping (satellite_radiation_data):
        - radiation_id (PK, AUTO_INCREMENT)
        - location_id (FK to locations)
        - model_id (FK to weather_models)
        - valid_date (DATE) - derived from start_date/end_date
        - shortwave_radiation_mean (DECIMAL)
        - direct_radiation_mean (DECIMAL)
        - diffuse_radiation_mean (DECIMAL)
        - direct_normal_irradiance_mean (DECIMAL) - DNI
        - global_tilted_irradiance_mean (DECIMAL) - GTI
        - terrestrial_radiation_mean (DECIMAL)
        - data_quality_score (DECIMAL) - calculated from valid_records ratio
        - created_at (TIMESTAMP)
        - UNIQUE KEY: (location_id, model_id, observation_date)
        
        Args:
            location_id: Location ID
            processed_data: Processed statistics from _process_satellite_data
            start_date: Start date of data range
            end_date: End date of data range
        
        Returns:
            True if saved successfully
        
        Explanation:
        - Uses ON DUPLICATE KEY UPDATE to update existing row
        - Calculates data_quality_score from valid_records ratio
        - observation_date uses end_date or current date
        """
        
        # Calculate data quality score (0-100%)
        total = processed_data.get('total_records', 1)
        valid = processed_data.get('valid_records', 0)
        quality_score = round((valid / total) * 100, 2) if total > 0 else 0
        
        if quality_score > 75:
            quality_flag = 'good'
            
        elif quality_score > 50:
            quality_flag = 'fair'
            
        else:
            quality_flag = 'poor'
        
        # Use end_date as observation_date, or default to today
        observation_date = end_date if end_date else start_date
        
        query = """
        INSERT INTO satellite_radiation_daily (
            location_id, model_id, valid_date,
            shortwave_radiation, direct_radiation, 
            diffuse_radiation, direct_normal_irradiance, global_tilted_irradiance,
            terrestrial_radiation, panel_tilt_angle, panel_azimuth_angle, quality_flag,
            created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON DUPLICATE KEY UPDATE
            shortwave_radiation = VALUES(shortwave_radiation),
            direct_radiation = VALUES(direct_radiation),
            diffuse_radiation = VALUES(diffuse_radiation),
            direct_normal_irradiance = VALUES(direct_normal_irradiance),
            global_tilted_irradiance = VALUES(global_tilted_irradiance),
            terrestrial_radiation = VALUES(terrestrial_radiation),
            quality_flag = VALUES(quality_flag)
        """
        
        params = (
            location_id,
            self.satellite_model_id,
            observation_date,
            processed_data.get('shortwave_radiation_mean'),
            processed_data.get('direct_radiation_mean'),
            processed_data.get('diffuse_radiation_mean'),
            processed_data.get('dni_mean'),
            processed_data.get('gti_mean'),
            processed_data.get('terrestrial_radiation_mean'),
            tilt,
            azimuth,
            quality_flag,
        )
        
        try:
            self.db.execute_insert(query, params)
            self.logger.info(
                f"✓ Satellite radiation data saved for location {location_id} "
                f"(date: {observation_date}, quality: {quality_score}%)"
            )
            return True
        except Exception as e:
            self._log_db_error("save_satellite_data", e)
            return False
        
        
    def get_daily_satellite_radiation(
        self,
        location_id: int,
        days: int = 7
    ) -> Optional[list]:
        """
        Get daily satellite radiation data for a location
        
        Args:
            location_id: Location ID
            days: Number of days to retrieve (default: 7, max: 365)
        
        Returns:
            List of dictionaries with daily radiation data or None
        
        Example:
            >>> service = SatelliteService()
            >>> daily = service.get_daily_satellite_radiation(location_id=1, days=7)
            >>> print(f"Found {len(daily)} radiation records")
            >>> print(daily[0]['shortwave_radiation'])
            245.5
        """
        
        query = """
        SELECT 
            srd.radiation_id,
            srd.location_id,
            srd.model_id,
            srd.valid_date,
            srd.shortwave_radiation,
            srd.direct_radiation,
            srd.diffuse_radiation,
            srd.direct_normal_irradiance,
            srd.global_tilted_irradiance,
            srd.terrestrial_radiation,
            srd.panel_tilt_angle,
            srd.panel_azimuth_angle,
            srd.quality_flag,
            srd.created_at,
            wm.model_name,
            wm.model_code
        FROM satellite_radiation_daily srd
        LEFT JOIN weather_models wm ON srd.model_id = wm.model_id
        WHERE srd.location_id = %s
            AND srd.valid_date >= CURDATE() - INTERVAL %s DAY
            AND srd.valid_date <= CURDATE()
        ORDER BY srd.valid_date DESC
        """
        
        try:
            results = self.db.execute_query(query, (location_id, days))
            
            if not results:
                self.logger.warning(f"No satellite radiation data found for location {location_id}")
                return None
            
            daily_data = []
            for row in results:
                daily_data.append({
                    "radiation_id": row[0],
                    "location_id": row[1],
                    "model_id": row[2],
                    "valid_date": row[3].isoformat() if row[3] else None,
                    "shortwave_radiation": float(row[4]) if row[4] is not None else None,
                    "direct_radiation": float(row[5]) if row[5] is not None else None,
                    "diffuse_radiation": float(row[6]) if row[6] is not None else None,
                    "direct_normal_irradiance": float(row[7]) if row[7] is not None else None,
                    "global_tilted_irradiance": float(row[8]) if row[8] is not None else None,
                    "terrestrial_radiation": float(row[9]) if row[9] is not None else None,
                    "panel_tilt_angle": row[10],
                    "panel_azimuth_angle": row[11],
                    "quality_flag": row[12],
                    "created_at": row[13].isoformat() if row[13] else None,
                    "model_name": row[14],
                    "model_code": row[15],
                })
            
            return daily_data
        
        except Exception as e:
            self._log_db_error("get_daily_satellite_radiation", e)
            return None


    def get_latest_satellite_radiation(self, location_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the most recent satellite radiation data for a location
        
        This serves as a "current" endpoint since satellite data is daily
        
        Args:
            location_id: Location ID
        
        Returns:
            Dictionary with latest radiation data or None
        
        Example:
            >>> service = SatelliteService()
            >>> latest = service.get_latest_satellite_radiation(location_id=1)
            >>> print(latest['shortwave_radiation'])
            245.5
            >>> print(latest['valid_date'])
            2025-11-07
        """
        
        query = """
        SELECT 
            srd.radiation_id,
            srd.location_id,
            srd.model_id,
            srd.valid_date,
            srd.shortwave_radiation,
            srd.direct_radiation,
            srd.diffuse_radiation,
            srd.direct_normal_irradiance,
            srd.global_tilted_irradiance,
            srd.terrestrial_radiation,
            srd.panel_tilt_angle,
            srd.panel_azimuth_angle,
            srd.quality_flag,
            srd.created_at,
            wm.model_name,
            wm.model_code
        FROM satellite_radiation_daily srd
        LEFT JOIN weather_models wm ON srd.model_id = wm.model_id
        WHERE srd.location_id = %s
        ORDER BY srd.valid_date DESC
        LIMIT 1
        """
        
        try:
            result = self.db.execute_query(query, (location_id,))
            
            if not result:
                self.logger.warning(f"No satellite radiation data found for location {location_id}")
                return None
            
            row = result[0]
            
            return {
                "radiation_id": row[0],
                "location_id": row[1],
                "model_id": row[2],
                "valid_date": row[3].isoformat() if row[3] else None,
                "shortwave_radiation": float(row[4]) if row[4] is not None else None,
                "direct_radiation": float(row[5]) if row[5] is not None else None,
                "diffuse_radiation": float(row[6]) if row[6] is not None else None,
                "direct_normal_irradiance": float(row[7]) if row[7] is not None else None,
                "global_tilted_irradiance": float(row[8]) if row[8] is not None else None,
                "terrestrial_radiation": float(row[9]) if row[9] is not None else None,
                "panel_tilt_angle": row[10],
                "panel_azimuth_angle": row[11],
                "quality_flag": row[12],
                "created_at": row[13].isoformat() if row[13] else None,
                "model_name": row[14],
                "model_code": row[15],
            }
        
        except Exception as e:
            self._log_db_error("get_latest_satellite_radiation", e)
            return None


    def get_all_satellite_data(
        self,
        location_id: int,
        days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Get all satellite radiation data for a location (latest + daily history)
        
        This is the main method used by the /satellite/all API endpoint
        
        Args:
            location_id: Location ID
            days: Number of days to retrieve (default: 7)
        
        Returns:
            Dictionary with all satellite data
        
        Example:
            >>> service = SatelliteService()
            >>> satellite = service.get_all_satellite_data(location_id=1)
            >>> print(satellite['latest']['shortwave_radiation'])
            245.5
            >>> print(len(satellite['daily']))
            7
        """
        
        try:
            
            
            result = {
                "success": True,
                "location_id": location_id,
                "latest": None,
                "daily": None,
                "statistics": None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Fetch latest radiation data (serves as "current")
            latest = self.get_latest_satellite_radiation(location_id)
            if latest:
                result["latest"] = latest
            
            # Fetch daily history
            daily = self.get_daily_satellite_radiation(location_id, days=days)
            if daily:
                result["daily"] = daily
                result["daily_count"] = len(daily)
            
            # Get statistics for the period
            statistics = self.get_satellite_statistics(
                location_id=location_id,
                start_date=None,  # Will use available data range
                end_date=None
            )
            if statistics:
                result["statistics"] = statistics
            
            # Check if we got any data
            if not latest and not daily:
                self.logger.warning(f"No satellite data found for location {location_id}")
                return None
            
            return result
        
        except Exception as e:
            self._log_db_error("get_all_satellite_data", e)
            return None
        
    def get_satellite_statistics(
        self,
        location_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregated satellite radiation statistics for a location
        
        Args:
            location_id: Location ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with statistics or None
        
        Example Output:
            {
                'location_id': 1,
                'total_days': 31,
                'avg_shortwave': 245.5,
                'avg_dni': 210.8,
                'avg_gti': 250.1,
                'max_dni': 850.2,
                'min_dni': 50.3,
                'date_range': '2024-01-01 to 2024-01-31'
            }
        """
        
        try:
            where_conditions = ["location_id = %s"]
            params = [location_id]
            
            if start_date:
                where_conditions.append("valid_date >= %s")
                params.append(start_date)
            
            if end_date:
                where_conditions.append("valid_date <= %s")
                params.append(end_date)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
            SELECT 
                COUNT(*) as total_days,
                AVG(shortwave_radiation) as avg_shortwave,
                AVG(direct_radiation) as avg_direct,
                AVG(diffuse_radiation) as avg_diffuse,
                AVG(direct_normal_irradiance) as avg_dni,
                AVG(global_tilted_irradiance) as avg_gti,
                AVG(terrestrial_radiation) as avg_terrestrial,
                MAX(direct_normal_irradiance) as max_dni,
                MIN(direct_normal_irradiance) as min_dni,
                MIN(valid_date) as min_date,
                MAX(valid_date) as max_date
            FROM satellite_radiation_daily
            WHERE {where_clause}
            """
            
            result = self.db.execute_query(query, params)
            
            if not result or not result[0][0]:
                return None
            
            row = result[0]
            
            return {
                'location_id': location_id,
                'total_days': row[0],
                'avg_shortwave_radiation': round(float(row[1]), 2) if row[1] else None,
                'avg_direct_radiation': round(float(row[2]), 2) if row[2] else None,
                'avg_diffuse_radiation': round(float(row[3]), 2) if row[3] else None,
                'avg_dni': round(float(row[4]), 2) if row[4] else None,
                'avg_gti': round(float(row[5]), 2) if row[5] else None,
                'avg_terrestrial_radiation': round(float(row[6]), 2) if row[6] else None,
                'max_dni': round(float(row[7]), 2) if row[7] else None,
                'min_dni': round(float(row[8]), 2) if row[8] else None,
                'date_range': f"{row[9]} to {row[10]}" if row[9] and row[10] else None
            }
        
        except Exception as e:
            self._log_db_error("get_satellite_statistics", e)
            return None
        
        
    