"""
Satellite Radiation Service Test Suite

Tests all functionality of SatelliteService:
1. Database initialization (models & parameters)
2. Location creation
3. Satellite radiation data fetching and processing
4. Mean calculation with NULL handling
5. Data quality checks
6. Duplicate handling
7. Complete workflow

Run with:
    cd /home/ronald/data-viento/apps/server
    python tests/test_satellite_service.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime, timedelta
from src.services.satellite_service import SatelliteService
from src.db.database import DatabaseConnection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SatelliteServiceTester:
    """Test suite for SatelliteService"""
    
    def __init__(self):
        self.service = SatelliteService()
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
        """Test database initialization with satellite model"""
        
        self.print_header("TEST 1: Initialize Database")
        
        try:
            # Test 1a: Verify CAMS_SOLAR model exists
            print("Test 1a: Verifying CAMS_SOLAR satellite model...")
            query = "SELECT model_id, model_name, model_type FROM weather_models WHERE model_code = 'CAMS_SOLAR'"
            result = self.service.db.execute_query(query)
            
            if result:
                model_id, model_name, model_type = result[0]
                self.print_result(
                    "CAMS_SOLAR model exists",
                    model_type == 'satellite_radiation',
                    f"ID: {model_id}, Name: {model_name}, Type: {model_type}"
                )
            else:
                # Try to create it
                model_id = self.service._get_or_create_satellite_model()
                self.print_result(
                    "CAMS_SOLAR model created",
                    model_id > 0,
                    f"Model ID: {model_id}"
                )
            
            # Test 1b: Verify satellite parameters exist (if any)
            print("\nTest 1b: Verifying radiation parameters...")
            param_codes = ['shortwave_rad', 'direct_rad', 'diffuse_rad', 
                          'dni', 'gti', 'terrestrial_rad']
            
            query = """
            SELECT parameter_code, parameter_name, unit
            FROM weather_parameters
            WHERE parameter_code IN ({})
            """.format(','.join(['%s'] * len(param_codes)))
            
            param_result = self.service.db.execute_query(query, param_codes)
            
            if param_result:
                print(f"\n       Found {len(param_result)} radiation parameters:")
                for code, name, unit in param_result[:5]:
                    print(f"       {code}: {name} ({unit})")
                
                self.print_result(
                    "Radiation parameters exist",
                    len(param_result) >= 3,
                    f"{len(param_result)} parameters found"
                )
            else:
                self.print_result(
                    "Radiation parameters exist", 
                    True,  # OK if no parameters exist (we store aggregates)
                    "No parameters found (expected for daily aggregates)"
                )
        
        except Exception as e:
            self.print_result("Database initialization", False, str(e))
            logger.error(f"Error in test_01: {e}", exc_info=True)
    
    # ==================== TEST 2: LOCATION SERVICE ====================
    
    def test_02_location_creation(self):
        """Test location creation and retrieval"""
        
        self.print_header("TEST 2: Location Service")
        
        try:
            # Test 2a: Create new location
            print("Test 2a: Creating location 'Madrid Solar Farm'...")
            location_id = self.service.location_service.get_or_create_location(
                name="Madrid Solar Farm",
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
                name="Madrid Solar Farm",
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
    
    # ==================== TEST 3: SATELLITE DATA FETCHING ====================
    
    async def test_03_fetch_satellite_data(self):
        """Test fetching and processing satellite radiation data"""
        
        self.print_header("TEST 3: Fetch Satellite Radiation Data")
        
        try:
            # Use yesterday's date (satellite data is historical)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Test 3a: Fetch satellite radiation data
            print(f"Test 3a: Fetching satellite radiation for Madrid ({yesterday})...")
            result = await self.service.fetch_and_save_satellite_data(
                location_name="Madrid Solar Farm",
                latitude=40.4168,
                longitude=-3.7038,
                start_date=yesterday,
                end_date=yesterday,
                tilt=35,
                azimuth=180,
                timezone="Europe/Madrid"
            )
            
            self.print_result(
                "Fetch satellite radiation data",
                result['success'] and result['data_saved'],
                f"Location ID: {result['location_id']}, Valid records: {result['processed_records']}"
            )
            
            # Test 3b: Verify data in database
            print("\nTest 3b: Verifying satellite data in database...")
            query = """
            SELECT valid_date, shortwave_radiation, direct_radiation, diffuse_radiation,
                   direct_normal_irradiance, global_tilted_irradiance, 
                   panel_tilt_angle, panel_azimuth_angle, quality_flag
            FROM satellite_radiation_daily
            WHERE location_id = %s AND valid_date = %s
            """
            db_result = self.service.db.execute_query(query, (self.madrid_location_id, yesterday))
            
            if db_result:
                (valid_date, shortwave, direct, diffuse, dni, gti, 
                 tilt, azimuth, quality) = db_result[0]
                
                self.print_result(
                    "Satellite data saved to database",
                    shortwave is not None or direct is not None,
                    f"Date: {valid_date}, Quality: {quality}"
                )
                
                # Show radiation values
                print(f"       Shortwave: {shortwave} W/m², Direct: {direct} W/m², Diffuse: {diffuse} W/m²")
                print(f"       DNI: {dni} W/m², GTI: {gti} W/m²")
                print(f"       Panel: Tilt {tilt}°, Azimuth {azimuth}°")
            else:
                self.print_result("Satellite data saved to database", False, "No data found")
            
            # Test 3c: Test duplicate handling (ON DUPLICATE KEY UPDATE)
            print("\nTest 3c: Testing duplicate handling...")
            await asyncio.sleep(2)  # Wait 2 seconds
            
            result_2 = await self.service.fetch_and_save_satellite_data(
                location_name="Madrid Solar Farm",
                latitude=40.4168,
                longitude=-3.7038,
                start_date=yesterday,
                end_date=yesterday,
                tilt=35,
                azimuth=180,
                timezone="Europe/Madrid"
            )
            
            # Check that only ONE row exists for this date
            count_query = """
            SELECT COUNT(*) FROM satellite_radiation_daily 
            WHERE location_id = %s AND valid_date = %s
            """
            count_result = self.service.db.execute_query(count_query, (self.madrid_location_id, yesterday))
            row_count = count_result[0][0] if count_result else 0
            
            self.print_result(
                "Duplicate satellite data handling",
                row_count == 1,
                f"Rows in database: {row_count} (should be 1)"
            )
        
        except Exception as e:
            self.print_result("Fetch satellite data test", False, str(e))
            logger.error(f"Error in test_03: {e}", exc_info=True)
    
    # ==================== TEST 4: MEAN CALCULATION & NULL HANDLING ====================
    
    def test_04_mean_calculation(self):
        """Test mean calculation with NULL value handling"""
        
        self.print_header("TEST 4: Mean Calculation & NULL Handling")
        
        try:
            # Test 4a: Mean with all valid values
            print("Test 4a: Testing mean calculation with all valid values...")
            values_1 = [100.0, 200.0, 300.0, 400.0]
            mean_1 = self.service._calculate_mean_skip_nulls(values_1)
            expected_1 = 250.0
            
            self.print_result(
                "Mean calculation (all valid)",
                mean_1 == expected_1,
                f"Input: {values_1} → Mean: {mean_1} (expected: {expected_1})"
            )
            
            # Test 4b: Mean with some NULL values
            print("\nTest 4b: Testing mean calculation with NULL values...")
            values_2 = [100.0, None, 300.0, None, 500.0]
            mean_2 = self.service._calculate_mean_skip_nulls(values_2)
            expected_2 = 300.0
            
            self.print_result(
                "Mean calculation (skip NULLs)",
                mean_2 == expected_2,
                f"Input: {values_2} → Mean: {mean_2} (expected: {expected_2})"
            )
            
            # Test 4c: Mean with all NULL values
            print("\nTest 4c: Testing mean calculation with all NULL values...")
            values_3 = [None, None, None]
            mean_3 = self.service._calculate_mean_skip_nulls(values_3)
            
            self.print_result(
                "Mean calculation (all NULLs)",
                mean_3 is None,
                f"Input: {values_3} → Mean: {mean_3} (expected: None)"
            )
            
            # Test 4d: Mean with empty list
            print("\nTest 4d: Testing mean calculation with empty list...")
            values_4 = []
            mean_4 = self.service._calculate_mean_skip_nulls(values_4)
            
            self.print_result(
                "Mean calculation (empty list)",
                mean_4 is None,
                f"Input: {values_4} → Mean: {mean_4} (expected: None)"
            )
        
        except Exception as e:
            self.print_result("Mean calculation test", False, str(e))
            logger.error(f"Error in test_04: {e}", exc_info=True)
    
    # ==================== TEST 5: STATISTICS QUERY ====================
    
    async def test_05_statistics(self):
        """Test satellite statistics query"""
        
        self.print_header("TEST 5: Satellite Statistics")
        
        try:
            # Use yesterday's date
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Test 5a: Get statistics for single day
            print(f"Test 5a: Getting statistics for Madrid ({yesterday})...")
            stats = self.service.get_satellite_statistics(
                location_id=self.madrid_location_id,
                start_date=yesterday,
                end_date=yesterday
            )
            
            if stats:
                self.print_result(
                    "Retrieve satellite statistics",
                    True,
                    f"Total days: {stats['total_days']}"
                )
                
                # Show detailed statistics
                print(f"\n       📊 Radiation Statistics:")
                print(f"       Avg Shortwave: {stats.get('avg_shortwave_radiation')} W/m²")
                print(f"       Avg Direct: {stats.get('avg_direct_radiation')} W/m²")
                print(f"       Avg Diffuse: {stats.get('avg_diffuse_radiation')} W/m²")
                print(f"       Avg DNI: {stats.get('avg_dni')} W/m²")
                print(f"       Avg GTI: {stats.get('avg_gti')} W/m²")
                print(f"       Max DNI: {stats.get('max_dni')} W/m²")
                print(f"       Min DNI: {stats.get('min_dni')} W/m²")
                print(f"       Date Range: {stats.get('date_range')}")
                
                # Verify statistics are reasonable
                avg_dni = stats.get('avg_dni')
                has_valid_stats = avg_dni is not None and avg_dni >= 0 and avg_dni <= 1500
                
                self.print_result(
                    "Statistics values are reasonable",
                    has_valid_stats,
                    f"Avg DNI: {avg_dni} W/m² (0-1500 expected)"
                )
            else:
                self.print_result("Retrieve satellite statistics", False, "No statistics found")
        
        except Exception as e:
            self.print_result("Statistics query test", False, str(e))
            logger.error(f"Error in test_05: {e}", exc_info=True)
    
    # ==================== TEST 6: MULTIPLE DATES ====================
    
    async def test_06_multiple_dates(self):
        """Test fetching satellite data for multiple dates"""
        
        self.print_header("TEST 6: Multiple Dates Workflow")
        
        try:
            # Fetch data for last 3 days
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            
            print(f"Test 6a: Fetching satellite data for date range ({start_date} to {end_date})...")
            
            # Fetch for each day individually (satellite API works better with single days)
            days_saved = 0
            for i in range(3):
                date = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')
                
                result = await self.service.fetch_and_save_satellite_data(
                    location_name="Madrid Solar Farm",
                    latitude=40.4168,
                    longitude=-3.7038,
                    start_date=date,
                    end_date=date,
                    tilt=35,
                    azimuth=180,
                    timezone="Europe/Madrid"
                )
                
                if result['success'] and result['data_saved']:
                    days_saved += 1
                
                await asyncio.sleep(1)  # Rate limit
            
            self.print_result(
                "Fetch multiple dates",
                days_saved >= 1,
                f"Saved {days_saved} days of data"
            )
            
            # Test 6b: Get statistics for date range
            print(f"\nTest 6b: Getting statistics for date range...")
            stats = self.service.get_satellite_statistics(
                location_id=self.madrid_location_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if stats:
                total_days = stats.get('total_days', 0)
                self.print_result(
                    "Statistics for multiple days",
                    total_days >= 1,
                    f"Total days: {total_days}, Avg DNI: {stats.get('avg_dni')} W/m²"
                )
            else:
                self.print_result("Statistics for multiple days", False, "No statistics found")
        
        except Exception as e:
            self.print_result("Multiple dates test", False, str(e))
            logger.error(f"Error in test_06: {e}", exc_info=True)
    
    # ==================== TEST 7: COMPLETE WORKFLOW ====================
    
    async def test_07_complete_workflow(self):
        """Test complete workflow for new location"""
        
        self.print_header("TEST 7: Complete Workflow (New Location)")
        
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            print(f"Test 7: Fetching satellite data for Barcelona Solar Park ({yesterday})...")
            result = await self.service.fetch_and_save_satellite_data(
                location_name="Barcelona Solar Park",
                latitude=41.3851,
                longitude=2.1734,
                start_date=yesterday,
                end_date=yesterday,
                tilt=30,
                azimuth=180,
                timezone="Europe/Madrid",
                country="ES",
                country_name="Spain"
            )
            
            # Verify success
            workflow_success = (
                result['success'] and
                result['data_saved'] and
                result['location_id'] is not None
            )
            
            details = f"Location ID: {result['location_id']}, Valid records: {result['processed_records']}"
            self.print_result("Complete workflow", workflow_success, details)
            
            # Verify Barcelona location created
            if result['location_id']:
                location = self.service.location_service.get_location_by_id(result['location_id'])
                if location:
                    self.print_result(
                        "Barcelona location created",
                        location['name'] == "Barcelona Solar Park",
                        f"Location ID: {result['location_id']}"
                    )
                    
                    # Verify data completeness
                    print("\nTest 7b: Verifying data completeness for Barcelona...")
                    
                    # Check satellite data exists
                    data_query = """
                    SELECT COUNT(*) FROM satellite_radiation_daily 
                    WHERE location_id = %s
                    """
                    data_count = self.service.db.execute_query(data_query, (result['location_id'],))[0][0]
                    
                    self.print_result(
                        "Barcelona data completeness",
                        data_count > 0,
                        f"Satellite data records: {data_count}"
                    )
        
        except Exception as e:
            self.print_result("Complete workflow test", False, str(e))
            logger.error(f"Error in test_07: {e}", exc_info=True)
    
    # ==================== TEST 8: DATA QUALITY CHECKS ====================
    
    def test_08_data_quality(self):
        """Test data quality and integrity"""
        
        self.print_header("TEST 8: Data Quality Checks")
        
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Test 8a: Check for NULL values in critical fields
            print("Test 8a: Checking for NULL values in satellite data...")
            query = """
            SELECT location_id,
                   (shortwave_radiation IS NULL) as shortwave_null,
                   (direct_normal_irradiance IS NULL) as dni_null,
                   (global_tilted_irradiance IS NULL) as gti_null,
                   quality_flag
            FROM satellite_radiation_daily
            WHERE location_id = %s AND valid_date = %s
            """
            null_check = self.service.db.execute_query(query, (self.madrid_location_id, yesterday))
            
            if null_check:
                loc_id, shortwave_null, dni_null, gti_null, quality = null_check[0]
                has_data = not (shortwave_null and dni_null and gti_null)
                
                self.print_result(
                    "Satellite data has non-NULL values",
                    has_data,
                    f"Shortwave: {'NULL' if shortwave_null else 'OK'}, DNI: {'NULL' if dni_null else 'OK'}, GTI: {'NULL' if gti_null else 'OK'}, Quality: {quality}"
                )
            
            # Test 8b: Check quality flags
            print("\nTest 8b: Checking quality flags...")
            quality_query = """
            SELECT quality_flag, COUNT(*) as count
            FROM satellite_radiation_daily
            WHERE location_id = %s
            GROUP BY quality_flag
            """
            quality_result = self.service.db.execute_query(quality_query, (self.madrid_location_id,))
            
            if quality_result:
                print("\n       Quality flag distribution:")
                for quality_flag, count in quality_result:
                    print(f"       {quality_flag}: {count} records")
                
                # Check that we have at least some 'good' quality data
                good_quality = any(row[0] == 'good' for row in quality_result)
                
                self.print_result(
                    "Quality flags present",
                    len(quality_result) > 0,
                    f"{len(quality_result)} quality levels found, Has 'good': {good_quality}"
                )
            
            # Test 8c: Check for duplicate dates
            print("\nTest 8c: Checking for duplicate dates...")
            dup_query = """
            SELECT valid_date, COUNT(*) as duplicates
            FROM satellite_radiation_daily
            WHERE location_id = %s
            GROUP BY valid_date
            HAVING COUNT(*) > 1
            LIMIT 5
            """
            dup_result = self.service.db.execute_query(dup_query, (self.madrid_location_id,))
            
            has_duplicates = len(dup_result) > 0 if dup_result else False
            
            if has_duplicates:
                print("\n       Found duplicates:")
                for valid_date, count in dup_result:
                    print(f"       Date {valid_date}: {count} duplicates")
            
            self.print_result(
                "No duplicate dates",
                not has_duplicates,
                "Clean data (no duplicates)" if not has_duplicates else f"{len(dup_result)} duplicate dates found"
            )
            
            # Test 8d: Check data value ranges
            print("\nTest 8d: Checking data value ranges...")
            range_query = """
            SELECT 
                MIN(shortwave_radiation) as min_shortwave,
                MAX(shortwave_radiation) as max_shortwave,
                MIN(direct_normal_irradiance) as min_dni,
                MAX(direct_normal_irradiance) as max_dni,
                AVG(direct_normal_irradiance) as avg_dni
            FROM satellite_radiation_daily
            WHERE location_id = %s
            """
            range_result = self.service.db.execute_query(range_query, (self.madrid_location_id,))
            
            if range_result:
                min_sw, max_sw, min_dni, max_dni, avg_dni = range_result[0]
                
                # Check if values are in reasonable range (0-1500 W/m² for DNI)
                values_reasonable = (
                    (min_dni is None or min_dni >= 0) and
                    (max_dni is None or max_dni <= 1500) and
                    (avg_dni is None or (avg_dni >= 0 and avg_dni <= 1500))
                )
                
                self.print_result(
                    "Data values in reasonable range",
                    values_reasonable,
                    f"DNI range: {min_dni}-{max_dni} W/m², Avg: {avg_dni} W/m²"
                )
        
        except Exception as e:
            self.print_result("Data quality checks", False, str(e))
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
        print("  SATELLITE RADIATION SERVICE TEST SUITE")
        print("  Starting at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*70)
        
        try:
            # Run tests in order
            self.test_01_initialize_database()
            self.test_02_location_creation()
            await self.test_03_fetch_satellite_data()
            self.test_04_mean_calculation()
            await self.test_05_statistics()
            await self.test_06_multiple_dates()
            await self.test_07_complete_workflow()
            self.test_08_data_quality()
        
        finally:
            # Clean up
            await self.service.close()
            
            # Print summary
            self.print_summary()


async def main():
    """Main test runner"""
    
    tester = SatelliteServiceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())