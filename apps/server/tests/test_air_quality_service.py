"""
Air Quality Service Test Suite

Tests all functionality of AirQualityService:
1. Database initialization (models & parameters)
2. Location creation
3. Current air quality fetching and saving
4. Hourly forecast fetching and saving
5. Duplicate handling
6. Complete workflow

Run with:
    cd /home/ronald/data-viento/apps/server
    python tests/test_air_quality_service.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime
from src.services.air_quality_service import AirQualityService
from src.db.database import DatabaseConnection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class AirQualityServiceTester:
    """Test suite for AirQualityService"""
    
    def __init__(self):
        self.service = AirQualityService()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def print_header(self, title: str):
        """Print formatted test header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70 + "\n")
    
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"       {details}")
        
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {details}")
    
    # ==================== TEST 1: DATABASE INITIALIZATION ====================
    
    def test_01_initialize_database(self):
        """Test database initialization with air quality model"""
        
        self.print_header("TEST 1: Initialize Database")
        
        try:
            # Test 1a: Verify CAMS_EUROPE model exists
            print("Test 1a: Verifying CAMS_EUROPE air quality model...")
            query = "SELECT model_id, model_name, model_type FROM weather_models WHERE model_code = 'CAMS_EUROPE'"
            result = self.service.db.execute_query(query)
            
            if result:
                model_id, model_name, model_type = result[0]
                self.print_result(
                    "CAMS_EUROPE model exists",
                    model_type == 'air_quality',
                    f"ID: {model_id}, Name: {model_name}, Type: {model_type}"
                )
            else:
                # Try to create it
                model_id = self.service._get_or_create_air_quality_model()
                self.print_result(
                    "CAMS_EUROPE model created",
                    model_id > 0,
                    f"Model ID: {model_id}"
                )
            
            # Test 1b: Verify air quality parameters exist
            print("\nTest 1b: Verifying air quality parameters...")
            param_codes = ['pm2_5', 'pm10', 'aqi_european', 'aqi_us', 'no2', 'o3', 'so2', 'co']
            
            query = """
            SELECT parameter_code, parameter_name, unit
            FROM weather_parameters
            WHERE parameter_code IN ({})
            """.format(','.join(['%s'] * len(param_codes)))
            
            param_result = self.service.db.execute_query(query, param_codes)
            
            if param_result:
                print(f"\n       Found {len(param_result)} air quality parameters:")
                for code, name, unit in param_result[:5]:
                    print(f"       {code}: {name} ({unit})")
                
                self.print_result(
                    "Air quality parameters exist",
                    len(param_result) >= 5,
                    f"{len(param_result)} parameters found"
                )
            else:
                self.print_result("Air quality parameters exist", False, "No parameters found")
        
        except Exception as e:
            self.print_result("Database initialization", False, str(e))
            logger.error(f"Error in test_01: {e}", exc_info=True)
    
    # ==================== TEST 2: LOCATION SERVICE ====================
    
    def test_02_location_creation(self):
        """Test location creation and retrieval"""
        
        self.print_header("TEST 2: Location Service")
        
        try:
            # Test 2a: Create new location
            print("Test 2a: Creating location 'Madrid'...")
            location_id = self.service.location_service.get_or_create_location(
                name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                timezone="Europe/Madrid",
                country="ES",
                country_name="Spain"
            )
            
            self.print_result(
                "Create location",
                location_id > 0,
                f"Location ID: {location_id}"
            )
            
            # Test 2b: Get existing location (should not create duplicate)
            print("\nTest 2b: Retrieving existing location...")
            location_id_2 = self.service.location_service.get_or_create_location(
                name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Get existing location (no duplicate)",
                location_id == location_id_2,
                f"Both IDs: {location_id} == {location_id_2}"
            )
            
            # Test 2c: Verify location data
            print("\nTest 2c: Verifying location data...")
            location = self.service.location_service.get_location_by_id(location_id)
            
            if location:
                self.print_result(
                    "Retrieve location by ID",
                    True,
                    f"Name: {location['name']}, Coords: ({location['latitude']}, {location['longitude']})"
                )
            else:
                self.print_result("Retrieve location by ID", False, "Location not found")
            
            # Store for later tests
            self.madrid_location_id = location_id
        
        except Exception as e:
            self.print_result("Location creation", False, str(e))
            logger.error(f"Error in test_02: {e}", exc_info=True)
    
    # ==================== TEST 3: CURRENT AIR QUALITY ====================
    
    async def test_03_current_air_quality(self):
        """Test fetching and saving current air quality"""
        
        self.print_header("TEST 3: Current Air Quality")
        
        try:
            # Test 3a: Fetch current air quality
            print("Test 3a: Fetching current air quality for Madrid...")
            result = await self.service.fetch_and_save_air_quality(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=True,
                include_hourly=False,
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch current air quality",
                result['success'] and result['current_saved'],
                f"Location ID: {result['location_id']}"
            )
            
            # Test 3b: Verify data in database
            print("\nTest 3b: Verifying current air quality in database...")
            query = """
            SELECT pm2_5, pm10, european_aqi, us_aqi, nitrogen_dioxide, ozone, observation_time
            FROM air_quality_current
            WHERE location_id = %s
            """
            db_result = self.service.db.execute_query(query, (self.madrid_location_id,))
            
            if db_result:
                pm25, pm10, eu_aqi, us_aqi, no2, o3, obs_time = db_result[0]
                self.print_result(
                    "Current air quality saved to database",
                    pm25 is not None or pm10 is not None,
                    f"PM2.5: {pm25}, PM10: {pm10}, EU AQI: {eu_aqi}, US AQI: {us_aqi}, Time: {obs_time}"
                )
                
                # Additional detail output
                if no2 is not None or o3 is not None:
                    print(f"       NO2: {no2} µg/m³, O3: {o3} µg/m³")
            else:
                self.print_result("Current air quality saved to database", False, "No data found")
            
            # Test 3c: Test duplicate handling (ON DUPLICATE KEY UPDATE)
            print("\nTest 3c: Testing duplicate handling...")
            await asyncio.sleep(2)  # Wait 2 seconds
            
            result_2 = await self.service.fetch_and_save_air_quality(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=True,
                include_hourly=False,
                timezone="Europe/Madrid"
            )
            
            # Check that only ONE row exists
            count_query = "SELECT COUNT(*) FROM air_quality_current WHERE location_id = %s"
            count_result = self.service.db.execute_query(count_query, (self.madrid_location_id,))
            row_count = count_result[0][0] if count_result else 0
            
            self.print_result(
                "Duplicate current air quality handling",
                row_count == 1,
                f"Rows in database: {row_count} (should be 1)"
            )
        
        except Exception as e:
            self.print_result("Current air quality test", False, str(e))
            logger.error(f"Error in test_03: {e}", exc_info=True)
    
    # ==================== TEST 4: HOURLY AIR QUALITY FORECAST ====================
    
    async def test_04_hourly_forecast(self):
        """Test fetching and saving hourly air quality forecast"""
        
        self.print_header("TEST 4: Hourly Air Quality Forecast")
        
        try:
            # Test 4a: Fetch hourly forecast
            print("Test 4a: Fetching hourly air quality forecast for Madrid...")
            result = await self.service.fetch_and_save_air_quality(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=False,
                include_hourly=True,
                forecast_days=3,  # 3 days of hourly data
                domains="auto",
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch hourly air quality forecast",
                result['success'] and result['hourly_saved'],
                "Hourly forecast fetched and saved"
            )
            
            # Test 4b: Verify forecast batch created
            print("\nTest 4b: Verifying forecast batch in database...")
            query = """
            SELECT air_quality_id, forecast_reference_time, data_domain, timezone
            FROM air_quality_forecasts
            WHERE location_id = %s
            ORDER BY forecast_reference_time DESC
            LIMIT 1
            """
            forecast_result = self.service.db.execute_query(query, (self.madrid_location_id,))
            
            if forecast_result:
                forecast_id, ref_time, domain, tz = forecast_result[0]
                self.print_result(
                    "Forecast batch created",
                    True,
                    f"Forecast ID: {forecast_id}, Time: {ref_time}, Domain: {domain}, TZ: {tz}"
                )
                
                # Test 4c: Verify forecast data points
                print("\nTest 4c: Verifying forecast data points...")
                data_query = """
                SELECT COUNT(*), COUNT(DISTINCT parameter_id)
                FROM air_quality_data
                WHERE air_quality_id = %s
                """
                data_result = self.service.db.execute_query(data_query, (forecast_id,))
                
                if data_result:
                    total_rows, unique_params = data_result[0]
                    self.print_result(
                        "Forecast data points saved",
                        total_rows > 0,
                        f"{total_rows} data points, {unique_params} parameters"
                    )
                    
                    # Test 4d: Show sample data
                    print("\nTest 4d: Sample forecast data...")
                    sample_query = """
                    SELECT p.parameter_name, aqd.valid_time, aqd.value, aqd.unit, aqd.quality_flag
                    FROM air_quality_data aqd
                    JOIN weather_parameters p ON aqd.parameter_id = p.parameter_id
                    WHERE aqd.air_quality_id = %s
                    ORDER BY aqd.valid_time ASC, p.parameter_name ASC
                    LIMIT 10
                    """
                    sample_result = self.service.db.execute_query(sample_query, (forecast_id,))
                    
                    if sample_result:
                        print("\n       Sample data points:")
                        for param_name, valid_time, value, unit, quality in sample_result[:5]:
                            print(f"       {valid_time} | {param_name}: {value} {unit} [{quality}]")
                        
                        self.print_result("Sample data retrieved", True, f"{len(sample_result)} samples shown")
                    
                    # Test 4e: Verify specific parameters
                    print("\nTest 4e: Verifying parameter coverage...")
                    param_query = """
                    SELECT DISTINCT p.parameter_code, p.parameter_name
                    FROM air_quality_data aqd
                    JOIN weather_parameters p ON aqd.parameter_id = p.parameter_id
                    WHERE aqd.air_quality_id = %s
                    ORDER BY p.parameter_code
                    """
                    param_result = self.service.db.execute_query(param_query, (forecast_id,))
                    
                    if param_result:
                        print("\n       Parameters saved:")
                        for code, name in param_result:
                            print(f"       • {code}: {name}")
                        
                        expected_params = {'pm2_5', 'pm10', 'no2', 'o3'}
                        found_params = {row[0] for row in param_result}
                        has_core_params = expected_params.issubset(found_params)
                        
                        self.print_result(
                            "Core air quality parameters present",
                            has_core_params,
                            f"Found: {', '.join(found_params)}"
                        )
            else:
                self.print_result("Forecast batch created", False, "No forecast batch found")
        
        except Exception as e:
            self.print_result("Hourly forecast test", False, str(e))
            logger.error(f"Error in test_04: {e}", exc_info=True)
    
    # ==================== TEST 5: COMPLETE WORKFLOW ====================
    
    async def test_05_complete_workflow(self):
        """Test complete workflow with current + hourly"""
        
        self.print_header("TEST 5: Complete Workflow (Current + Hourly)")
        
        try:
            print("Test 5: Fetching ALL air quality data for Barcelona...")
            result = await self.service.fetch_and_save_air_quality(
                location_name="Barcelona",
                latitude=41.3851,
                longitude=2.1734,
                include_current=True,
                include_hourly=True,
                forecast_days=5,
                domains="cams_europe",
                timezone="Europe/Madrid",
                country="ES",
                country_name="Spain"
            )
            
            # Verify all succeeded
            all_saved = (
                result['success'] and
                result['current_saved'] and
                result['hourly_saved']
            )
            
            details = f"Current: {result['current_saved']}, Hourly: {result['hourly_saved']}"
            self.print_result("Complete workflow", all_saved, details)
            
            # Verify Barcelona location created
            if result['location_id']:
                location = self.service.location_service.get_location_by_id(result['location_id'])
                if location:
                    self.print_result(
                        "Barcelona location created",
                        location['name'] == "Barcelona",
                        f"Location ID: {result['location_id']}"
                    )
                    
                    # Verify both current and forecast data exist
                    print("\nTest 5b: Verifying data completeness for Barcelona...")
                    
                    # Check current air quality
                    current_query = "SELECT COUNT(*) FROM air_quality_current WHERE location_id = %s"
                    current_count = self.service.db.execute_query(current_query, (result['location_id'],))[0][0]
                    
                    # Check forecast data
                    forecast_query = """
                    SELECT COUNT(DISTINCT aqf.air_quality_id), COUNT(aqd.data_id)
                    FROM air_quality_forecasts aqf
                    LEFT JOIN air_quality_data aqd ON aqf.air_quality_id = aqd.air_quality_id
                    WHERE aqf.location_id = %s
                    """
                    forecast_result = self.service.db.execute_query(forecast_query, (result['location_id'],))
                    forecast_batches, data_points = forecast_result[0] if forecast_result else (0, 0)
                    
                    self.print_result(
                        "Barcelona data completeness",
                        current_count > 0 and data_points > 0,
                        f"Current records: {current_count}, Forecast batches: {forecast_batches}, Data points: {data_points}"
                    )
        
        except Exception as e:
            self.print_result("Complete workflow test", False, str(e))
            logger.error(f"Error in test_05: {e}", exc_info=True)
    
    # ==================== TEST 6: DATA QUALITY CHECKS ====================
    
    async def test_06_data_quality(self):
        """Test data quality and integrity"""
        
        self.print_header("TEST 6: Data Quality Checks")
        
        try:
            # Test 6a: Check for NULL values in critical fields
            print("Test 6a: Checking for NULL values in current air quality...")
            query = """
            SELECT location_id,
                   (pm2_5 IS NULL) as pm25_null,
                   (pm10 IS NULL) as pm10_null,
                   (european_aqi IS NULL) as eu_aqi_null
            FROM air_quality_current
            WHERE location_id = %s
            """
            null_check = self.service.db.execute_query(query, (self.madrid_location_id,))
            
            if null_check:
                loc_id, pm25_null, pm10_null, eu_aqi_null = null_check[0]
                has_data = not (pm25_null and pm10_null and eu_aqi_null)
                
                self.print_result(
                    "Current air quality has non-NULL values",
                    has_data,
                    f"PM2.5: {'NULL' if pm25_null else 'OK'}, PM10: {'NULL' if pm10_null else 'OK'}, EU AQI: {'NULL' if eu_aqi_null else 'OK'}"
                )
            
            # Test 6b: Check timestamp freshness
            print("\nTest 6b: Checking timestamp freshness...")
            time_query = """
            SELECT observation_time,
                   TIMESTAMPDIFF(MINUTE, observation_time, NOW()) as minutes_old
            FROM air_quality_current
            WHERE location_id = %s
            """
            time_result = self.service.db.execute_query(time_query, (self.madrid_location_id,))
            
            if time_result:
                obs_time, minutes_old = time_result[0]
                is_fresh = minutes_old < 60  # Less than 1 hour old
                
                self.print_result(
                    "Observation timestamp is fresh",
                    is_fresh,
                    f"Last observation: {obs_time} ({minutes_old} minutes ago)"
                )
            
            # Test 6c: Check for duplicate forecast data
            print("\nTest 6c: Checking for duplicate forecast data...")
            dup_query = """
            SELECT air_quality_id, parameter_id, valid_time, COUNT(*) as duplicates
            FROM air_quality_data
            WHERE air_quality_id IN (
                SELECT air_quality_id FROM air_quality_forecasts
                WHERE location_id = %s
            )
            GROUP BY air_quality_id, parameter_id, valid_time
            HAVING COUNT(*) > 1
            LIMIT 5
            """
            dup_result = self.service.db.execute_query(dup_query, (self.madrid_location_id,))
            
            has_duplicates = len(dup_result) > 0 if dup_result else False
            
            if has_duplicates:
                print("\n       Found duplicates:")
                for aq_id, param_id, valid_time, count in dup_result:
                    print(f"       AQ_ID {aq_id}, Param {param_id}, Time {valid_time}: {count} duplicates")
            
            self.print_result(
                "No duplicate forecast data",
                not has_duplicates,
                "Clean data (no duplicates)" if not has_duplicates else f"{len(dup_result)} duplicate groups found"
            )
        
        except Exception as e:
            self.print_result("Data quality checks", False, str(e))
            logger.error(f"Error in test_06: {e}", exc_info=True)
    
    # ==================== TEST 7: CLEANUP OPERATIONS ====================
    
    def test_07_cleanup(self):
        """Test cleanup operations"""
        
        self.print_header("TEST 7: Cleanup Operations")
        
        try:
            # Test 7a: Count existing forecasts
            print("Test 7a: Counting existing forecasts...")
            count_query = "SELECT COUNT(*) FROM air_quality_forecasts"
            initial_count = self.service.db.execute_query(count_query)[0][0]
            
            print(f"       Initial forecast count: {initial_count}")
            
            # Test 7b: Test cleanup (keep last 7 days)
            print("\nTest 7b: Testing cleanup_old_forecasts (keep 7 days)...")
            deleted = self.service.cleanup_old_forecasts(days_to_keep=7)
            
            self.print_result(
                "Cleanup old forecasts",
                deleted >= 0,
                f"Deleted {deleted} old forecast batches"
            )
            
            # Test 7c: Test data point cleanup
            print("\nTest 7c: Testing cleanup_old_forecast_data_points (keep 168 hours)...")
            deleted_points = self.service.cleanup_old_forecast_data_points(hours_to_keep=168)
            
            self.print_result(
                "Cleanup old data points",
                deleted_points >= 0,
                f"Deleted {deleted_points} old data points"
            )
        
        except Exception as e:
            self.print_result("Cleanup operations", False, str(e))
            logger.error(f"Error in test_07: {e}", exc_info=True)
    
    # ==================== TEST SUMMARY ====================
    
    def print_summary(self):
        """Print test summary"""
        
        self.print_header("TEST SUMMARY")
        
        total = self.test_results['passed'] + self.test_results['failed']
        
        print(f"Total Tests: {total}")
        print(f"✓ Passed: {self.test_results['passed']}")
        print(f"✗ Failed: {self.test_results['failed']}")
        
        if self.test_results['failed'] > 0:
            print("\nFailed Tests:")
            for error in self.test_results['errors']:
                print(f"  • {error}")
        
        print("\n" + "="*70)
        
        if self.test_results['failed'] == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {self.test_results['failed']} test(s) failed")
        
        print("="*70 + "\n")
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        
        print("\n" + "="*70)
        print("  AIR QUALITY SERVICE TEST SUITE")
        print("  Starting at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*70)
        
        try:
            # Run tests in order
            self.test_01_initialize_database()
            self.test_02_location_creation()
            await self.test_03_current_air_quality()
            await self.test_04_hourly_forecast()
            await self.test_05_complete_workflow()
            await self.test_06_data_quality()
            self.test_07_cleanup()
        
        finally:
            # Clean up
            await self.service.close()
            
            # Print summary
            self.print_summary()


async def main():
    """Main test runner"""
    
    tester = AirQualityServiceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())


