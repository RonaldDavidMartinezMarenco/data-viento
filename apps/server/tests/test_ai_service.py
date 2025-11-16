"""
AI Service Test

Test the AI service with different types of queries
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from src.services.ai_service import AIService

def test_ai_chat():
    """Basic AI chat test"""
    
    print("\n" + "="*70)
    print("  AI CHAT SERVICE TEST")
    print("="*70 + "\n")
    
    # Initialize service
    print("Initializing AIService...")
    ai_service = AIService()
    print("✓ Service initialized\n")
    
    # Test data
    test_user_id = 10  # Make sure this user exists
    test_location_id = 1  # Bogota
    
    # Simulate chart data (weather daily)
    test_chart_data = [
        {
            'valid_date': '2024-01-15',
            'temperature_2m_max': 18.5,
            'temperature_2m_min': 8.2,
            'precipitation_sum': 0.0,
            'location_id': 1,
            'model_name': 'ICON-D2'
        },
        {
            'valid_date': '2024-01-16',
            'temperature_2m_max': 20.1,
            'temperature_2m_min': 9.5,
            'precipitation_sum': 2.5,
            'location_id': 1,
            'model_name': 'ICON-D2'
        },
        {
            'valid_date': '2024-01-17',
            'temperature_2m_max': 17.3,
            'temperature_2m_min': 7.8,
            'precipitation_sum': 5.2,
            'location_id': 1,
            'model_name': 'ICON-D2'
        }
    ]
    
    # Test 1: Simple temperature question
    print("Test 1: Question about maximum temperature")
    print("-" * 70)
    
    try:
        response = ai_service.chat(
            user_id=test_user_id,
            query_text="What is the maximum temperature in the next few days?",
            location_id=test_location_id,
            chart_type='weather_daily',
            chart_id='weatherTempChart',
            chart_data=test_chart_data,
            session_id='test_session_1'
        )
        
        print("✓ Response received:")
        print(f"  Query ID: {response['query_id']}")
        print(f"  Intent: {response['intent']}")
        print(f"  Entities: {response['entities']}")
        print(f"  Time: {response['processing_time_ms']}ms")
        print(f"  Tokens: {response['tokens_used']}")
        print(f"\n  AI Response:")
        print(f"  {response['response']}\n")
        
    except Exception as e:
        print(f"✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Question about precipitation
    print("Test 2: Question about rain")
    print("-" * 70)
    
    try:
        response = ai_service.chat(
            user_id=test_user_id,
            query_text="Will it rain tomorrow?",
            location_id=test_location_id,
            chart_type='weather_daily',
            chart_id='weatherPrecipChart',
            chart_data=test_chart_data,
            session_id='test_session_1'
        )
        
        print("✓ Response received:")
        print(f"  Intent: {response['intent']}")
        print(f"\n  AI Response:")
        print(f"  {response['response']}\n")
        
    except Exception as e:
        print(f"✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: General question (no chart context)
    print("Test 3: General theoretical question")
    print("-" * 70)
    
    try:
        response = ai_service.chat(
            user_id=test_user_id,
            query_text="What is UV index and why is it important?",
            location_id=None,
            chart_type='general',
            chart_id=None,
            chart_data=None,
            session_id='test_session_1'
        )
        
        print("✓ Response received:")
        print(f"  Intent: {response['intent']}")
        print(f"\n  AI Response:")
        print(f"  {response['response']}\n")
        
    except Exception as e:
        print(f"✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Verify database
    print("Test 4: Verify queries in database")
    print("-" * 70)
    
    try:
        query = """
        SELECT query_id, query_text, intent_detected, 
               processing_time_ms, tokens_used, created_at
        FROM user_queries
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
        """
        
        results = ai_service.db.execute_query(query, (test_user_id,))
        
        if results:
            print(f"✓ Found {len(results)} queries in database:\n")
            for row in results:
                query_id, text, intent, time_ms, tokens, created = row
                print(f"  ID {query_id}:")
                print(f"    Question: {text[:50]}...")
                print(f"    Intent: {intent}")
                print(f"    Time: {time_ms}ms, Tokens: {tokens}")
                print(f"    Created: {created}\n")
        else:
            print("✗ No queries found in database\n")
            return False
        
    except Exception as e:
        print(f"✗ Error verifying database: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    print("="*70)
    print("  ✓ ALL TESTS PASSED")
    print("="*70 + "\n")
    
    return True

def test_data_filtering():
    """Test chart data filtering"""
    
    print("\n" + "="*70)
    print("  DATA FILTERING TEST")
    print("="*70 + "\n")
    
    ai_service = AIService()
    
    # Test daily data filtering
    print("Test 1: Daily data filtering (weatherTempChart)")
    print("-" * 70)
    
    daily_data = [
        {
            'forecast_day_id': 347,
            'location_id': 1,
            'model_id': 1,
            'valid_date': '2025-11-16',
            'temperature_2m_max': 15,
            'temperature_2m_min': 12.6,
            'precipitation_sum': 15.2,
            'precipitation_hours': 15,
            'precipitation_probability_max': 90,
            'weather_code': 95,
            'sunrise': '2025-11-16T00:45:00',
            'sunset': '2025-11-16T12:38:00',
            'sunshine_duration': 5816,
            'uv_index_max': 6,
            'wind_speed_10m_max': 7.4,
            'wind_gusts_10m_max': 19.1,
            'wind_direction_10m_dominant': 231,
            'model_name': 'Open-Meteo Forecast Model'
        }
    ]
    
    filtered = ai_service.filter_chart_data('weatherTempChart', daily_data)
    
    print("Original fields:", list(daily_data[0].keys()))
    print("Filtered fields:", list(filtered[0].keys()))
    
    expected_fields = {'valid_date', 'temperature_2m_max', 'temperature_2m_min', 'location_id', 'model_name'}
    actual_fields = set(filtered[0].keys())
    
    if expected_fields == actual_fields:
        print("✓ Daily filtering working correctly\n")
    else:
        print(f"✗ Daily filtering failed")
        print(f"  Expected: {expected_fields}")
        print(f"  Got: {actual_fields}\n")
        return False
    
    # Test hourly data filtering
    print("Test 2: Hourly data filtering (weatherHourlyTempChart)")
    print("-" * 70)
    
    hourly_data = {
        'forecast_id': 851,
        'location_id': 1,
        'forecast_reference_time': '2025-11-16T12:00:07',
        'parameters': {
            'temp_2m': {
                'name': 'Temperature 2m',
                'unit': '°C',
                'times': ['2025-11-16T00:00:00', '2025-11-16T01:00:00'],
                'values': [12.7, 13.0]
            },
            'humidity_2m': {
                'name': 'Relative Humidity 2m',
                'unit': '%',
                'times': ['2025-11-16T00:00:00', '2025-11-16T01:00:00'],
                'values': [96, 94]
            },
            'precip': {
                'name': 'Precipitation',
                'unit': 'mm',
                'times': ['2025-11-16T00:00:00', '2025-11-16T01:00:00'],
                'values': [0.2, 0]
            },
            'wind_speed_10m': {
                'name': 'Wind Speed 10m',
                'unit': 'km/h',
                'times': ['2025-11-16T00:00:00', '2025-11-16T01:00:00'],
                'values': [1.8, 0.8]
            }
        }
    }
    
    filtered = ai_service.filter_chart_data('weatherHourlyTempChart', hourly_data)
    
    print("Original parameters:", list(hourly_data['parameters'].keys()))
    print("Filtered parameters:", list(filtered['parameters'].keys()))
    
    expected_params = {'temp_2m', 'humidity_2m'}
    actual_params = set(filtered['parameters'].keys())
    
    if expected_params == actual_params:
        print("✓ Hourly filtering working correctly\n")
    else:
        print(f"✗ Hourly filtering failed")
        print(f"  Expected: {expected_params}")
        print(f"  Got: {actual_params}\n")
        return False
    
    print("="*70)
    print("  ✓ ALL FILTERING TESTS PASSED")
    print("="*70 + "\n")
    
    return True

def test_context_building():
    """Test context building"""
    
    print("\n" + "="*70)
    print("  CONTEXT BUILDING TEST")
    print("="*70 + "\n")
    
    ai_service = AIService()
    
    # Test daily context
    print("Test 1: Daily context building")
    print("-" * 70)
    
    daily_data = [
        {
            'valid_date': '2025-11-16',
            'temperature_2m_max': 15,
            'temperature_2m_min': 12.6,
            'location_id': 1,
            'model_name': 'Open-Meteo Forecast Model'
        },
        {
            'valid_date': '2025-11-17',
            'temperature_2m_max': 15.6,
            'temperature_2m_min': 12.6,
            'location_id': 1,
            'model_name': 'Open-Meteo Forecast Model'
        },
        {
            'valid_date': '2025-11-18',
            'temperature_2m_max': 16.3,
            'temperature_2m_min': 12.6,
            'location_id': 1,
            'model_name': 'Open-Meteo Forecast Model'
        }
    ]
    
    context = ai_service._build_daily_context(
        data=daily_data,
        chart_name='Daily Temperature',
        location='Bogota, Colombia'
    )
    
    print("Generated context:")
    print(context)
    
    # Verify context contains key elements
    if all(keyword in context for keyword in ['Location:', 'Chart:', 'Period:', 'Data Points:', 'Statistical Summary:']):
        print("\n✓ Daily context building working correctly\n")
    else:
        print("\n✗ Daily context missing key elements\n")
        return False
    
    # Test hourly context
    print("Test 2: Hourly context building")
    print("-" * 70)
    
    hourly_data = {
        'forecast_id': 851,
        'location_id': 1,
        'forecast_reference_time': '2025-11-16T12:00:07',
        'parameters': {
            'temp_2m': {
                'name': 'Temperature 2m',
                'unit': '°C',
                'times': ['2025-11-16T00:00:00', '2025-11-16T01:00:00', '2025-11-16T02:00:00'],
                'values': [12.7, 13.0, 12.7]
            },
            'humidity_2m': {
                'name': 'Relative Humidity 2m',
                'unit': '%',
                'times': ['2025-11-16T00:00:00', '2025-11-16T01:00:00', '2025-11-16T02:00:00'],
                'values': [96, 94, 94]
            }
        }
    }
    
    context = ai_service._build_hourly_context(
        data=hourly_data,
        chart_name='Hourly Temperature & Humidity',
        location='Bogota, Colombia'
    )
    
    print("Generated context:")
    print(context)
    
    # Verify context contains key elements
    if all(keyword in context for keyword in ['Location:', 'Chart:', 'Period:', 'Parameters:', 'Current:', 'Max:', 'Min:', 'Avg:']):
        print("\n✓ Hourly context building working correctly\n")
    else:
        print("\n✗ Hourly context missing key elements\n")
        return False
    
    print("="*70)
    print("  ✓ ALL CONTEXT TESTS PASSED")
    print("="*70 + "\n")
    
    return True

def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*70)
    print("  RUNNING ALL AI SERVICE TESTS")
    print("="*70 + "\n")
    
    tests = [
        ("Data Filtering", test_data_filtering),
        ("Context Building", test_context_building),
        ("AI Chat", test_ai_chat)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} test passed\n")
            else:
                failed += 1
                print(f"✗ {test_name} test failed\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} test crashed: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"  TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()