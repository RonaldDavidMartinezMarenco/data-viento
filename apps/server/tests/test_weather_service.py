"""
Weather Service Test Suite

Tests all functionality of WeatherService:
1. Database initialization (models & parameters)
2. Location creation
3. Current weather fetching and saving
4. Daily forecast fetching and saving
5. Hourly forecast fetching and saving
6. Duplicate handling

Run with:
    cd /home/ronald/data-viento/apps/server
    python tests/test_weather_service.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime
from src.services.weather_service import WeatherService
from src.db.database import DatabaseConnection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class WeatherServiceTester:
    """Test suite for WeatherService"""
    
    def __init__(self):
        self.service = WeatherService()
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
        """Test database initialization with models and parameters"""
        
        self.print_header("TEST 1: Initialize Database")
        
        try:
            # Test 1a: Initialize weather models
            print("Test 1a: Initializing weather models...")
            models_success = self.service.initialize_weather_models()
            
            if models_success:
                # Verify models were created
                query = "SELECT COUNT(*) FROM weather_models"
                result = self.service.db.execute_query(query)
                model_count = result[0][0] if result else 0
                
                self.print_result(
                    "Initialize weather models",
                    model_count > 0,
                    f"{model_count} models created"
                )
            else:
                self.print_result("Initialize weather models", False, "Failed to insert models")
            
            # Test 1b: Initialize weather parameters
            print("\nTest 1b: Initializing weather parameters...")
            params_success = self.service.initialize_weather_parameters()
            
            if params_success:
                # Verify parameters were created
                query = "SELECT COUNT(*) FROM weather_parameters"
                result = self.service.db.execute_query(query)
                param_count = result[0][0] if result else 0
                
                self.print_result(
                    "Initialize weather parameters",
                    param_count > 0,
                    f"{param_count} parameters created"
                )
            else:
                self.print_result("Initialize weather parameters", False, "Failed to insert parameters")
            
            # Test 1c: Verify OM_FORECAST model exists
            print("\nTest 1c: Verifying OM_FORECAST model...")
            query = "SELECT model_id, model_name FROM weather_models WHERE model_code = 'OM_FORECAST'"
            result = self.service.db.execute_query(query)
            
            if result:
                model_id, model_name = result[0]
                self.print_result(
                    "OM_FORECAST model exists",
                    True,
                    f"ID: {model_id}, Name: {model_name}"
                )
            else:
                self.print_result("OM_FORECAST model exists", False, "Model not found")
        
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
    
    # ==================== TEST 3: CURRENT WEATHER ====================
    
    async def test_03_current_weather(self):
        """Test fetching and saving current weather"""
        
        self.print_header("TEST 3: Current Weather")
        
        try:
            # Test 3a: Fetch current weather
            print("Test 3a: Fetching current weather for Madrid...")
            result = await self.service.fetch_and_save_weather(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=True,
                include_hourly=False,
                include_daily=False,
            )
            
            self.print_result(
                "Fetch current weather",
                result['success'] and result['current_saved'],
                f"Location ID: {result['location_id']}"
            )
            
            # Test 3b: Verify data in database
            print("\nTest 3b: Verifying current weather in database...")
            query = """
            SELECT temperature_2m, relative_humidity_2m, wind_speed_10m, observation_time
            FROM current_weather
            WHERE location_id = %s
            """
            db_result = self.service.db.execute_query(query, (self.madrid_location_id,))
            
            if db_result:
                temp, humidity, wind, obs_time = db_result[0]
                self.print_result(
                    "Current weather saved to database",
                    temp is not None,
                    f"Temp: {temp}°C, Humidity: {humidity}%, Wind: {wind} km/h, Time: {obs_time}"
                )
            else:
                self.print_result("Current weather saved to database", False, "No data found")
            
            # Test 3c: Test duplicate handling (ON DUPLICATE KEY UPDATE)
            print("\nTest 3c: Testing duplicate handling...")
            await asyncio.sleep(2)  # Wait 2 seconds
            
            result_2 = await self.service.fetch_and_save_weather(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=True,
                include_hourly=False,
                include_daily=False,
                timezone="Europe/Madrid"
            )
            
            # Check that only ONE row exists
            count_query = "SELECT COUNT(*) FROM current_weather WHERE location_id = %s"
            count_result = self.service.db.execute_query(count_query, (self.madrid_location_id,))
            row_count = count_result[0][0] if count_result else 0
            
            self.print_result(
                "Duplicate current weather handling",
                row_count == 1,
                f"Rows in database: {row_count} (should be 1)"
            )
        
        except Exception as e:
            self.print_result("Current weather test", False, str(e))
            logger.error(f"Error in test_03: {e}", exc_info=True)
    
    # ==================== TEST 4: DAILY FORECAST ====================
    
    async def test_04_daily_forecast(self):
        """Test fetching and saving daily forecast"""
        
        self.print_header("TEST 4: Daily Forecast")
        
        try:
            # Test 4a: Fetch 7-day forecast
            print("Test 4a: Fetching 7-day forecast for Madrid...")
            result = await self.service.fetch_and_save_weather(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=False,
                include_hourly=False,
                include_daily=True,
                forecast_days=7,
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch daily forecast",
                result['success'] and result['daily_saved'],
                f"Forecast days: {result.get('forecast_days', 0)}"
            )
            
            # Test 4b: Verify data in database
            print("\nTest 4b: Verifying daily forecast in database...")
            query = """
            SELECT valid_date, temperature_2m_max, temperature_2m_min, precipitation_sum
            FROM weather_forecasts_daily
            WHERE location_id = %s
            ORDER BY valid_date ASC
            LIMIT 7
            """
            db_result = self.service.db.execute_query(query, (self.madrid_location_id,))
            
            if db_result:
                print(f"\n       Found {len(db_result)} daily forecasts:")
                for row in db_result[:3]:  # Show first 3
                    date, temp_max, temp_min, precip = row
                    print(f"       {date}: Max {temp_max}°C, Min {temp_min}°C, Precip {precip}mm")
                
                self.print_result(
                    "Daily forecast saved to database",
                    len(db_result) >= 7,
                    f"{len(db_result)} days saved"
                )
            else:
                self.print_result("Daily forecast saved to database", False, "No data found")
            
            # Test 4c: Test duplicate handling (should NOT create duplicates)
            print("\nTest 4c: Testing duplicate daily forecast handling...")
            
            # Count rows before
            count_query = "SELECT COUNT(*) FROM weather_forecasts_daily WHERE location_id = %s"
            count_before = self.service.db.execute_query(count_query, (self.madrid_location_id,))[0][0]
            
            # Fetch again
            await self.service.fetch_and_save_weather(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=False,
                include_daily=True,
                forecast_days=7,
                timezone="Europe/Madrid"
            )
            
            # Count rows after
            count_after = self.service.db.execute_query(count_query, (self.madrid_location_id,))[0][0]
            
            self.print_result(
                "Duplicate daily forecast handling",
                count_after == count_before,
                f"Before: {count_before}, After: {count_after} (should be equal)"
            )
        
        except Exception as e:
            self.print_result("Daily forecast test", False, str(e))
            logger.error(f"Error in test_04: {e}", exc_info=True)
    
    # ==================== TEST 5: HOURLY FORECAST ====================
    
    async def test_05_hourly_forecast(self):
        """Test fetching and saving hourly forecast"""
        
        self.print_header("TEST 5: Hourly Forecast")
        
        try:
            # Test 5a: Fetch hourly forecast
            print("Test 5a: Fetching hourly forecast for Madrid...")
            result = await self.service.fetch_and_save_weather(
                location_name="Madrid",
                latitude=40.4168,
                longitude=-3.7038,
                include_current=False,
                include_hourly=True,
                include_daily=False,
                forecast_days=3,  # 3 days = 72 hours
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch hourly forecast",
                result['success'] and result['hourly_saved'],
                "Hourly data fetched and saved"
            )
            
            # Test 5b: Verify forecast batch created
            print("\nTest 5b: Verifying forecast batch in database...")
            query = """
            SELECT forecast_id, forecast_reference_time, timezone
            FROM weather_forecasts
            WHERE location_id = %s
            ORDER BY forecast_reference_time DESC
            LIMIT 1
            """
            forecast_result = self.service.db.execute_query(query, (self.madrid_location_id,))
            
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
                FROM forecast_data
                WHERE forecast_id = %s
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
                    SELECT p.parameter_name, fd.valid_time, fd.value, fd.unit
                    FROM forecast_data fd
                    JOIN weather_parameters p ON fd.parameter_id = p.parameter_id
                    WHERE fd.forecast_id = %s
                    ORDER BY fd.valid_time ASC, p.parameter_name ASC
                    LIMIT 10
                    """
                    sample_result = self.service.db.execute_query(sample_query, (forecast_id,))
                    
                    if sample_result:
                        print("\n       Sample data points:")
                        for param_name, valid_time, value, unit in sample_result[:5]:
                            print(f"       {valid_time} | {param_name}: {value} {unit}")
                        
                        self.print_result("Sample data retrieved", True, f"{len(sample_result)} samples shown")
            else:
                self.print_result("Forecast batch created", False, "No forecast batch found")
        
        except Exception as e:
            self.print_result("Hourly forecast test", False, str(e))
            logger.error(f"Error in test_05: {e}", exc_info=True)
    
    # ==================== TEST 6: COMPLETE WORKFLOW ====================
    
    async def test_06_complete_workflow(self):
        """Test complete workflow with all data types"""
        
        self.print_header("TEST 6: Complete Workflow (Current + Hourly + Daily)")
        
        try:
            print("Test 6: Fetching ALL data types for Barcelona...")
            result = await self.service.fetch_and_save_weather(
                location_name="Barcelona",
                latitude=41.3851,
                longitude=2.1734,
                include_current=True,
                include_hourly=True,
                include_daily=True,
                forecast_days=7,
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
            
            # Verify Barcelona location created
            if result['location_id']:
                location = self.service.location_service.get_location_by_id(result['location_id'])
                if location:
                    self.print_result(
                        "Barcelona location created",
                        location['name'] == "Barcelona",
                        f"Location ID: {result['location_id']}"
                    )
        
        except Exception as e:
            self.print_result("Complete workflow test", False, str(e))
            logger.error(f"Error in test_06: {e}", exc_info=True)
    
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
        print("  WEATHER SERVICE TEST SUITE")
        print("  Starting at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*70)
        
        try:
            # Run tests in order
            #self.test_01_initialize_database()
            self.test_02_location_creation()
            await self.test_03_current_weather()
            await self.test_04_daily_forecast()
            await self.test_05_hourly_forecast()
            await self.test_06_complete_workflow()
        
        finally:
            # Clean up
            await self.service.close()
            
            # Print summary
            self.print_summary()


async def main():
    """Main test runner"""
    
    tester = WeatherServiceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())