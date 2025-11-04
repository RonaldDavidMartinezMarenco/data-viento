"""
Marine Service Test Suite

Tests all functionality of MarineService:
1. Database initialization (models & parameters)
2. Location creation
3. Current marine conditions fetching and saving
4. Daily forecast fetching and saving
5. Hourly forecast fetching and saving
6. Duplicate handling
7. Complete workflow

Run with:
    cd /home/ronald/data-viento/apps/server
    python tests/test_marine_service.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime
from src.services.marine_service import MarineService
from src.db.database import DatabaseConnection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MarineServiceTester:
    """Test suite for MarineService"""
    
    def __init__(self):
        self.service = MarineService()
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
        """Test database initialization with marine model"""
        
        self.print_header("TEST 1: Initialize Database")
        
        try:
            # Test 1a: Verify OM_MARINE model exists
            print("Test 1a: Verifying OM_MARINE marine model...")
            query = "SELECT model_id, model_name, model_type FROM weather_models WHERE model_code = 'OM_MARINE'"
            result = self.service.db.execute_query(query)
            
            if result:
                model_id, model_name, model_type = result[0]
                self.print_result(
                    "OM_MARINE model exists",
                    model_type == 'marine',
                    f"ID: {model_id}, Name: {model_name}, Type: {model_type}"
                )
            else:
                # Try to create it
                model_id = self.service._get_or_create_marine_model()
                self.print_result(
                    "OM_MARINE model created",
                    model_id > 0,
                    f"Model ID: {model_id}"
                )
            
            # Test 1b: Verify marine parameters exist
            print("\nTest 1b: Verifying marine parameters...")
            param_codes = ['wave_height', 'wave_direction', 'wave_period', 'swell_wave_height', 'sea_temp']
            
            query = """
            SELECT parameter_code, parameter_name, unit
            FROM weather_parameters
            WHERE parameter_code IN ({})
            """.format(','.join(['%s'] * len(param_codes)))
            
            param_result = self.service.db.execute_query(query, param_codes)
            
            if param_result:
                print(f"\n       Found {len(param_result)} marine parameters:")
                for code, name, unit in param_result[:5]:
                    print(f"       {code}: {name} ({unit})")
                
                self.print_result(
                    "Marine parameters exist",
                    len(param_result) >= 3,
                    f"{len(param_result)} parameters found"
                )
            else:
                self.print_result("Marine parameters exist", False, "No parameters found")
        
        except Exception as e:
            self.print_result("Database initialization", False, str(e))
            logger.error(f"Error in test_01: {e}", exc_info=True)
    
    # ==================== TEST 2: LOCATION SERVICE ====================
    
    def test_02_location_creation(self):
        """Test location creation and retrieval"""
        
        self.print_header("TEST 2: Location Service")
        
        try:
            # Test 2a: Create new location
            print("Test 2a: Creating location 'Barcelona Coast'...")
            location_id = self.service.location_service.get_or_create_location(
                name="Barcelona Coast",
                latitude=41.3851,
                longitude=2.1734,
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
                name="Barcelona Coast",
                latitude=41.3851,
                longitude=2.1734,
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
            self.barcelona_location_id = location_id
        
        except Exception as e:
            self.print_result("Location creation", False, str(e))
            logger.error(f"Error in test_02: {e}", exc_info=True)
    
    # ==================== TEST 3: CURRENT MARINE CONDITIONS ====================
    
    async def test_03_current_marine(self):
        """Test fetching and saving current marine conditions"""
        
        self.print_header("TEST 3: Current Marine Conditions")
        
        try:
            # Test 3a: Fetch current marine conditions
            print("Test 3a: Fetching current marine conditions for Barcelona Coast...")
            result = await self.service.fetch_and_save_marine(
                location_name="Barcelona Coast",
                latitude=41.3851,
                longitude=2.1734,
                include_current=True,
                include_hourly=False,
                include_daily=False,
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch current marine conditions",
                result['success'] and result['current_saved'],
                f"Location ID: {result['location_id']}"
            )
            
            # Test 3b: Verify data in database
            print("\nTest 3b: Verifying current marine conditions in database...")
            query = """
            SELECT wave_height, wave_direction, wave_period, 
                   swell_wave_height, sea_surface_temperature, observation_time
            FROM marine_current
            WHERE location_id = %s
            """
            db_result = self.service.db.execute_query(query, (self.barcelona_location_id,))
            
            if db_result:
                wave_h, wave_dir, wave_p, swell_h, sea_temp, obs_time = db_result[0]
                self.print_result(
                    "Current marine conditions saved to database",
                    wave_h is not None or swell_h is not None,
                    f"Wave Height: {wave_h}m, Direction: {wave_dir}°, Period: {wave_p}s, Time: {obs_time}"
                )
                
                # Additional detail output
                if swell_h is not None or sea_temp is not None:
                    print(f"       Swell Height: {swell_h}m, Sea Temp: {sea_temp}°C")
            else:
                self.print_result("Current marine conditions saved to database", False, "No data found")
            
            # Test 3c: Test duplicate handling (ON DUPLICATE KEY UPDATE)
            print("\nTest 3c: Testing duplicate handling...")
            await asyncio.sleep(2)  # Wait 2 seconds
            
            result_2 = await self.service.fetch_and_save_marine(
                location_name="Barcelona Coast",
                latitude=41.3851,
                longitude=2.1734,
                include_current=True,
                include_hourly=False,
                include_daily=False,
                timezone="Europe/Madrid"
            )
            
            # Check that only ONE row exists
            count_query = "SELECT COUNT(*) FROM marine_current WHERE location_id = %s"
            count_result = self.service.db.execute_query(count_query, (self.barcelona_location_id,))
            row_count = count_result[0][0] if count_result else 0
            
            self.print_result(
                "Duplicate current marine conditions handling",
                row_count == 1,
                f"Rows in database: {row_count} (should be 1)"
            )
        
        except Exception as e:
            self.print_result("Current marine conditions test", False, str(e))
            logger.error(f"Error in test_03: {e}", exc_info=True)
    
    # ==================== TEST 4: DAILY MARINE FORECAST ====================
    
    async def test_04_daily_forecast(self):
        """Test fetching and saving daily marine forecast"""
        
        self.print_header("TEST 4: Daily Marine Forecast")
        
        try:
            # Test 4a: Fetch daily forecast
            print("Test 4a: Fetching daily marine forecast for Barcelona Coast...")
            result = await self.service.fetch_and_save_marine(
                location_name="Barcelona Coast",
                latitude=41.3851,
                longitude=2.1734,
                include_current=False,
                include_hourly=False,
                include_daily=True,
                forecast_days=5,
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch daily marine forecast",
                result['success'] and result['daily_saved'],
                f"Forecast Days: {result.get('forecast_days', 0)}"
            )
            
            # Test 4b: Verify daily forecast data
            print("\nTest 4b: Verifying daily forecast in database...")
            query = """
            SELECT valid_date, wave_height_max, wave_direction_dominant, 
                   swell_wave_height_max
            FROM marine_forecasts_daily
            WHERE location_id = %s
            ORDER BY valid_date ASC
            LIMIT 7
            """
            daily_result = self.service.db.execute_query(query, (self.barcelona_location_id,))
            
            if daily_result:
                print(f"\n       Found {len(daily_result)} daily forecast records:")
                for date, wave_max, wave_dir, swell_max in daily_result[:3]:
                    print(f"       {date} | Wave: {wave_max}m @ {wave_dir}°, Swell: {swell_max}m")
                
                self.print_result(
                    "Daily forecast data saved",
                    len(daily_result) > 0,
                    f"{len(daily_result)} days saved"
                )
            else:
                self.print_result("Daily forecast data saved", False, "No data found")
            
            # Test 4c: Test duplicate handling (ON DUPLICATE KEY UPDATE)
            print("\nTest 4c: Testing duplicate daily forecast handling...")
            result_2 = await self.service.fetch_and_save_marine(
                location_name="Barcelona Coast",
                latitude=41.3851,
                longitude=2.1734,
                include_current=False,
                include_hourly=False,
                include_daily=True,
                forecast_days=7,
                timezone="Europe/Madrid"
            )
            
            # Count should still be same (7 days)
            count_query = """
            SELECT COUNT(*) FROM marine_forecasts_daily 
            WHERE location_id = %s
            """
            count_result = self.service.db.execute_query(count_query, (self.barcelona_location_id,))
            row_count = count_result[0][0] if count_result else 0
            
            self.print_result(
                "Duplicate daily forecast handling",
                row_count == 7,
                f"Rows in database: {row_count} (should be 7)"
            )
        
        except Exception as e:
            self.print_result("Daily forecast test", False, str(e))
            logger.error(f"Error in test_04: {e}", exc_info=True)
    
    # ==================== TEST 5: HOURLY MARINE FORECAST ====================
    
    async def test_05_hourly_forecast(self):
        """Test fetching and saving hourly marine forecast"""
        
        self.print_header("TEST 5: Hourly Marine Forecast")
        
        try:
            # Test 5a: Fetch hourly forecast
            print("Test 5a: Fetching hourly marine forecast for Valencia Coast...")
            result = await self.service.fetch_and_save_marine(
                location_name="Valencia Coast",
                latitude=39.4699,
                longitude=-0.3763,
                include_current=False,
                include_hourly=True,
                include_daily=False,
                forecast_days=3,  # 3 days of hourly data
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch hourly marine forecast",
                result['success'] and result['hourly_saved'],
                "Hourly forecast fetched and saved"
            )
            
            # Get Valencia location ID
            valencia_location_id = result['location_id']
            
            # Test 5b: Verify forecast batch created
            print("\nTest 5b: Verifying forecast batch in database...")
            query = """
            SELECT marine_id, forecast_reference_time, timezone
            FROM marine_forecasts
            WHERE location_id = %s
            ORDER BY forecast_reference_time DESC
            LIMIT 1
            """
            forecast_result = self.service.db.execute_query(query, (valencia_location_id,))
            
            if forecast_result:
                forecast_id, ref_time, tz = forecast_result[0]
                self.print_result(
                    "Forecast batch created",
                    True,
                    f"Forecast ID: {forecast_id}, Time: {ref_time}, TZ: {tz}"
                )
                
                # Test 5c: Verify forecast data points
                print("\nTest 5c: Verifying forecast data points...")
                data_query = """
                SELECT COUNT(*), COUNT(DISTINCT parameter_id)
                FROM marine_data
                WHERE marine_id = %s
                """
                data_result = self.service.db.execute_query(data_query, (forecast_id,))
                
                if data_result:
                    total_rows, unique_params = data_result[0]
                    self.print_result(
                        "Forecast data points saved",
                        total_rows > 0,
                        f"{total_rows} data points, {unique_params} parameters"
                    )
                    
                    # Test 5d: Show sample data
                    print("\nTest 5d: Sample forecast data...")
                    sample_query = """
                    SELECT p.parameter_name, md.valid_time, md.value, md.unit, md.quality_flag
                    FROM marine_data md
                    JOIN weather_parameters p ON md.parameter_id = p.parameter_id
                    WHERE md.marine_id = %s
                    ORDER BY md.valid_time ASC, p.parameter_name ASC
                    LIMIT 10
                    """
                    sample_result = self.service.db.execute_query(sample_query, (forecast_id,))
                    
                    if sample_result:
                        print("\n       Sample data points:")
                        for param_name, valid_time, value, unit, quality in sample_result[:5]:
                            print(f"       {valid_time} | {param_name}: {value} {unit} [{quality}]")
                        
                        self.print_result("Sample data retrieved", True, f"{len(sample_result)} samples shown")
                    
                    # Test 5e: Verify specific parameters
                    print("\nTest 5e: Verifying parameter coverage...")
                    param_query = """
                    SELECT DISTINCT p.parameter_code, p.parameter_name
                    FROM marine_data md
                    JOIN weather_parameters p ON md.parameter_id = p.parameter_id
                    WHERE md.marine_id = %s
                    ORDER BY p.parameter_code
                    """
                    param_result = self.service.db.execute_query(param_query, (forecast_id,))
                    
                    if param_result:
                        print("\n       Parameters saved:")
                        for code, name in param_result:
                            print(f"       • {code}: {name}")
                        
                        expected_params = {'wave_height', 'wave_direction', 'wave_period'}
                        found_params = {row[0] for row in param_result}
                        has_core_params = expected_params.issubset(found_params)
                        
                        self.print_result(
                            "Core marine parameters present",
                            has_core_params,
                            f"Found: {', '.join(found_params)}"
                        )
            else:
                self.print_result("Forecast batch created", False, "No forecast batch found")
        
        except Exception as e:
            self.print_result("Hourly forecast test", False, str(e))
            logger.error(f"Error in test_05: {e}", exc_info=True)
    
    # ==================== TEST 6: COMPLETE WORKFLOW ====================
    
    async def test_06_complete_workflow(self):
        """Test complete workflow with current + daily + hourly"""
        
        self.print_header("TEST 6: Complete Workflow (Current + Daily + Hourly)")
        
        try:
            print("Test 6: Fetching ALL marine data for Málaga Coast...")
            result = await self.service.fetch_and_save_marine(
                location_name="Málaga Coast",
                latitude=36.7213,
                longitude=-4.4214,
                include_current=True,
                include_hourly=True,
                include_daily=True,
                forecast_days=5,
                timezone="Europe/Madrid",
                country="ES",
                country_name="Spain"
            )
            
            # Verify all succeeded
            all_saved = (
                result['success'] and
                result['current_saved'] and
                result['hourly_saved'] and
                result['daily_saved']
            )
            
            details = f"Current: {result['current_saved']}, Hourly: {result['hourly_saved']}, Daily: {result['daily_saved']}"
            self.print_result("Complete workflow", all_saved, details)
            
            # Verify Málaga location created
            if result['location_id']:
                location = self.service.location_service.get_location_by_id(result['location_id'])
                if location:
                    self.print_result(
                        "Málaga location created",
                        location['name'] == "Málaga Coast",
                        f"Location ID: {result['location_id']}"
                    )
                    
                    # Verify data completeness
                    print("\nTest 6b: Verifying data completeness for Málaga...")
                    
                    # Check current marine conditions
                    current_query = "SELECT COUNT(*) FROM marine_current WHERE location_id = %s"
                    current_count = self.service.db.execute_query(current_query, (result['location_id'],))[0][0]
                    
                    # Check daily forecast
                    daily_query = "SELECT COUNT(*) FROM marine_forecasts_daily WHERE location_id = %s"
                    daily_count = self.service.db.execute_query(daily_query, (result['location_id'],))[0][0]
                    
                    # Check hourly forecast data
                    forecast_query = """
                    SELECT COUNT(DISTINCT mf.marine_id), COUNT(md.data_id)
                    FROM marine_forecasts mf
                    LEFT JOIN marine_data md ON mf.marine_id = md.marine_id
                    WHERE mf.location_id = %s
                    """
                    forecast_result = self.service.db.execute_query(forecast_query, (result['location_id'],))
                    forecast_batches, data_points = forecast_result[0] if forecast_result else (0, 0)
                    
                    self.print_result(
                        "Málaga data completeness",
                        current_count > 0 and daily_count > 0 and data_points > 0,
                        f"Current: {current_count}, Daily: {daily_count}, Forecast batches: {forecast_batches}, Data points: {data_points}"
                    )
        
        except Exception as e:
            self.print_result("Complete workflow test", False, str(e))
            logger.error(f"Error in test_06: {e}", exc_info=True)
    
    # ==================== TEST 7: DATA QUALITY CHECKS ====================
    
    async def test_07_data_quality(self):
        """Test data quality and integrity"""
        
        self.print_header("TEST 7: Data Quality Checks")
        
        try:
            # Test 7a: Check for NULL values in critical fields
            print("Test 7a: Checking for NULL values in current marine conditions...")
            query = """
            SELECT location_id,
                   (wave_height IS NULL) as wave_h_null,
                   (wave_direction IS NULL) as wave_dir_null,
                   (sea_surface_temperature IS NULL) as temp_null
            FROM marine_current
            WHERE location_id = %s
            """
            null_check = self.service.db.execute_query(query, (self.barcelona_location_id,))
            
            if null_check:
                loc_id, wave_h_null, wave_dir_null, temp_null = null_check[0]
                has_data = not (wave_h_null and wave_dir_null and temp_null)
                
                self.print_result(
                    "Current marine conditions has non-NULL values",
                    has_data,
                    f"Wave Height: {'NULL' if wave_h_null else 'OK'}, Wave Dir: {'NULL' if wave_dir_null else 'OK'}, Temp: {'NULL' if temp_null else 'OK'}"
                )
            
            # Test 7b: Check timestamp freshness
            print("\nTest 7b: Checking timestamp freshness...")
            time_query = """
            SELECT observation_time,
                   TIMESTAMPDIFF(MINUTE, observation_time, NOW()) as minutes_old
            FROM marine_current
            WHERE location_id = %s
            """
            time_result = self.service.db.execute_query(time_query, (self.barcelona_location_id,))
            
            if time_result:
                obs_time, minutes_old = time_result[0]
                is_fresh = minutes_old < 60  # Less than 1 hour old
                
                self.print_result(
                    "Observation timestamp is fresh",
                    is_fresh,
                    f"Last observation: {obs_time} ({minutes_old} minutes ago)"
                )
            
            # Test 7c: Check for duplicate forecast data
            print("\nTest 7c: Checking for duplicate forecast data...")
            dup_query = """
            SELECT marine_id, parameter_id, valid_time, COUNT(*) as duplicates
            FROM marine_data
            WHERE marine_id IN (
                SELECT marine_id FROM marine_forecasts
                WHERE location_id = %s
            )
            GROUP BY marine_id, parameter_id, valid_time
            HAVING COUNT(*) > 1
            LIMIT 5
            """
            dup_result = self.service.db.execute_query(dup_query, (self.barcelona_location_id,))
            
            has_duplicates = len(dup_result) > 0 if dup_result else False
            
            if has_duplicates:
                print("\n       Found duplicates:")
                for marine_id, param_id, valid_time, count in dup_result:
                    print(f"       Marine_ID {marine_id}, Param {param_id}, Time {valid_time}: {count} duplicates")
            
            self.print_result(
                "No duplicate forecast data",
                not has_duplicates,
                "Clean data (no duplicates)" if not has_duplicates else f"{len(dup_result)} duplicate groups found"
            )
        
        except Exception as e:
            self.print_result("Data quality checks", False, str(e))
            logger.error(f"Error in test_07: {e}", exc_info=True)
    
    # ==================== TEST 8: CLEANUP OPERATIONS ====================
    
    def test_08_cleanup(self):
        """Test cleanup operations"""
        
        self.print_header("TEST 8: Cleanup Operations")
        
        try:
            # Test 8a: Count existing forecasts
            print("Test 8a: Counting existing forecasts...")
            count_query = "SELECT COUNT(*) FROM marine_forecasts"
            initial_count = self.service.db.execute_query(count_query)[0][0]
            
            print(f"       Initial forecast count: {initial_count}")
            
            # Test 8b: Test cleanup (keep last 7 days)
            print("\nTest 8b: Testing cleanup_old_forecasts (keep 7 days)...")
            deleted = self.service.cleanup_old_forecasts(days_to_keep=7)
            
            self.print_result(
                "Cleanup old forecasts",
                deleted >= 0,
                f"Deleted {deleted} old forecast batches"
            )
            
            # Test 8c: Test data point cleanup
            print("\nTest 8c: Testing cleanup_old_forecast_data_points (keep 168 hours)...")
            deleted_points = self.service.cleanup_old_forecast_data_points(hours_to_keep=168)
            
            self.print_result(
                "Cleanup old data points",
                deleted_points >= 0,
                f"Deleted {deleted_points} old data points"
            )
        
        except Exception as e:
            self.print_result("Cleanup operations", False, str(e))
            logger.error(f"Error in test_08: {e}", exc_info=True)
    
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
        print("  MARINE SERVICE TEST SUITE")
        print("  Starting at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*70)
        
        try:
            # Run tests in order
            self.test_01_initialize_database()
            self.test_02_location_creation()
            await self.test_03_current_marine()
            await self.test_04_daily_forecast()
            await self.test_05_hourly_forecast()
            await self.test_06_complete_workflow()
            await self.test_07_data_quality()
            self.test_08_cleanup()
        
        finally:
            # Clean up
            await self.service.close()
            
            # Print summary
            self.print_summary()


async def main():
    """Main test runner"""
    
    tester = MarineServiceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())