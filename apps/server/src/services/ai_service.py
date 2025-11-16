import sys
import os
import time
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv

from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import HTTPException
import google.generativeai as genai

from src.services.base_service import BaseService
from src.services.location_service import LocationService

# Load environment variables
config_dir = Path(__file__).parent 
env_path = config_dir.parent / '.env'
load_dotenv(env_path)
api_key = os.getenv('GEMINI_API_KEY')

class AIService(BaseService):
    """
    AI Service for intelligent weather data analysis and chat
    Uses Google Gemini for natural language processing
    """
    
    def __init__(self, db=None):
        super().__init__(db)
        self.location_service = LocationService(self.db)
        
        # Configure Gemini
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Chart data filters
        self.chart_filters = {
                # WEATHER DAILY
                'weatherTempChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'temperature_2m_max', 'temperature_2m_min'],
                    'name': 'Daily Temperature'
                },
                'weatherPrecipChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'precipitation_sum', 'precipitation_probability_max', 'precipitation_hours'],
                    'name': 'Daily Precipitation'
                },
                'weatherWindChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'wind_speed_10m_max', 'wind_gusts_10m_max', 'wind_direction_10m_dominant'],
                    'name': 'Daily Wind'
                },
                'weatherUvChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'uv_index_max', 'sunshine_duration'],
                    'name': 'Daily UV & Sunshine'
                },
                
                # WEATHER HOURLY
                'weatherHourlyTempChart': {
                    'type': 'hourly',
                    'parameters': ['temp_2m', 'humidity_2m'],
                    'name': 'Hourly Temperature & Humidity'
                },
                'weatherHourlyPrecipChart': {
                    'type': 'hourly',
                    'parameters': ['precip', 'precip_prob'],
                    'name': 'Hourly Precipitation'
                },
                'weatherHourlyWindChart': {
                    'type': 'hourly',
                    'parameters': ['wind_speed_10m', 'wind_dir_10m'],
                    'name': 'Hourly Wind'
                },
                
                # AIR QUALITY
                'airQualityAqiChart': {
                    'type': 'hourly',
                    'parameters': ['aqi_european', 'aqi_us'],
                    'name': 'Air Quality Index'
                },
                'airQualityPollutantsChart': {
                    'type': 'hourly',
                    'parameters': ['pm2_5', 'pm10', 'no2', 'o3'],
                    'name': 'Air Quality Pollutants'
                },
                'airQualitySecondaryChart': {
                    'type': 'hourly',
                    'parameters': ['so2', 'co'],
                    'name': 'Secondary Pollutants'
                },
                
                # MARINE DAILY
                'marineDailyWaveChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'wave_height_max', 'swell_wave_height_max', 'wind_wave_height_max'],
                    'name': 'Marine Daily Wave Heights'
                },
                'marineDailyPeriodChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'wave_period_max', 'wave_direction_dominant'],
                    'name': 'Marine Daily Wave Period'
                },
                
                # MARINE HOURLY
                'marineHourlyWaveChart': {
                    'type': 'hourly',
                    'parameters': ['wave_height', 'swell_wave_height', 'wind_wave_height', 'wave_direction'],
                    'name': 'Marine Hourly Wave Heights'
                },
                'marineHourlyPeriodChart': {
                    'type': 'hourly',
                    'parameters': ['wave_period', 'sea_temp'],
                    'name': 'Marine Hourly Period & Temperature'
                },
                
                # SATELLITE
                'satelliteDailyRadiationChart': {
                    'type': 'daily',
                    'fields': ['created_at', 'shortwave_radiation', 'direct_radiation', 'diffuse_radiation'],
                    'name': 'Solar Radiation Components'
                },
                'satelliteDailyIrradianceChart': {
                    'type': 'daily',
                    'fields': ['created_at', 'direct_normal_irradiance', 'global_tilted_irradiance', 'terrestrial_radiation'],
                    'name': 'Solar Irradiance (DNI/GTI)'
                },
                
                # CLIMATE
                'climateTempTrendsChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'temperature_2m_max', 'temperature_2m_mean', 'temperature_2m_min'],
                    'name': 'Climate Temperature Trends',
                    'sample_rate': 7  # Sample every 7 days
                },
                'climatePrecipHumidityChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'precipitation_sum', 'relative_humidity_2m_mean'],
                    'name': 'Climate Precipitation & Humidity',
                    'sample_rate': 7
                },
                'climateWindRadiationChart': {
                    'type': 'daily',
                    'fields': ['valid_date', 'wind_speed_10m_max', 'shortwave_radiation_sum'],
                    'name': 'Climate Wind & Radiation',
                    'sample_rate': 7
                }
            }   
    
    def filter_chart_data(
        self,
        chart_id: Optional[str],
        chart_data: Any
    ) -> Dict[str, Any]:
        """
        Filter chart data to only include relevant fields for the specific chart
        
        Args:
            chart_id: ID of the chart (e.g., 'weatherTempChart')
            chart_data: Raw data from frontend
            
        Returns:
            Filtered data with only necessary fields
        """
        if not chart_id or chart_id not in self.chart_filters:
            return chart_data  # Return original if no filter defined
        
        filter_config = self.chart_filters[chart_id]
        
        if filter_config['type'] == 'daily' and isinstance(chart_data, list):
            return self._filter_daily_data(chart_data, filter_config)
        
        elif filter_config['type'] == 'hourly' and isinstance(chart_data, dict):
            return self._filter_hourly_data(chart_data, filter_config)
        
        return chart_data
    
    def _filter_daily_data(
        self,
        data: List[Dict[str, Any]],
        filter_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter daily data (array format)"""
        
        fields = filter_config.get('fields', [])
        sample_rate = filter_config.get('sample_rate', 1)
        
        # Sample data if needed (for climate charts)
        if sample_rate > 1:
            data = [item for i, item in enumerate(data) if i % sample_rate == 0]
        
        # Filter fields
        filtered_data = []
        for item in data:
            filtered_item = {}
            for field in fields:
                if field in item:
                    filtered_item[field] = item[field]
            
            # Always include metadata
            filtered_item['location_id'] = item.get('location_id')
            filtered_item['model_name'] = item.get('model_name')
            
            filtered_data.append(filtered_item)
        
        return filtered_data
    
    def _filter_hourly_data(
        self,
        data: Dict[str, Any],
        filter_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter hourly data (parameters format)"""
        
        parameters = filter_config.get('parameters', [])
        
        filtered_data = {
            'forecast_id': data.get('forecast_id'),
            'location_id': data.get('location_id'),
            'forecast_reference_time': data.get('forecast_reference_time'),
            'parameters': {}
        }
        
        # Filter only needed parameters
        if 'parameters' in data:
            for param in parameters:
                if param in data['parameters']:
                    filtered_data['parameters'][param] = data['parameters'][param]
        
        return filtered_data
    
    # Context Builders
    def _build_context(
        self,
        chart_type: Optional[str],
        chart_id: Optional[str],
        chart_data: Any,
        location_name: Optional[str]
    ) -> str:
        """Build context string from filtered chart data"""
        
        if not chart_id or not chart_data:
            return f"Location: {location_name or 'Unknown'}"
        
        # Get chart info
        chart_info = self.chart_filters.get(chart_id, {})
        chart_name = chart_info.get('name', chart_type)
        
        if isinstance(chart_data, dict) and 'daily_data' in chart_data:
            chart_data = chart_data['daily_data']
            if not chart_data or len(chart_data) == 0:
                return f"Location: {location_name}\nChart: {chart_name}\nNo climate data available"
            
        # Filter data
        filtered_data = self.filter_chart_data(chart_id, chart_data)
        
        # Build context based on type
        if chart_info.get('type') == 'daily':
            return self._build_daily_context(filtered_data, chart_name, location_name)
        elif chart_info.get('type') == 'hourly':
            return self._build_hourly_context(filtered_data, chart_name, location_name)
        
        return f"Location: {location_name}\nChart: {chart_name}"
    
    def _build_daily_context(
    self,
    data: List[Dict[str, Any]],
    chart_name: str,
    location: str
) -> str:
        """Build context for daily data"""
        
        if not data or len(data) == 0:
            return f"Location: {location}\nChart: {chart_name}\nNo data available"
        
        # Extract date range
        start_date = data[0].get('valid_date') or data[0].get('created_at')
        end_date = data[-1].get('valid_date') or data[-1].get('created_at')
        
        # Detect if this is a climate chart
        is_climate_chart = 'climate' in chart_name.lower()
        
        # Build basic header
        context = f"""
        Location: {location}
        Chart: {chart_name}
        Period: {start_date} to {end_date}
        Data Points: {len(data)}
        """
        
        # ========================================
        # FOR CLIMATE: ONLY STATISTICS (NO SAMPLE DATA)
        # ========================================
        if is_climate_chart:
            context += "\n⚠️ Long-term climate projection - Statistical summary only:\n"
            context += self._add_daily_stats_compact(data)
            
            # Add trend summary
            context += "\nTrend Analysis:\n"
            context += self._add_climate_trends(data)
        
        # ========================================
        # FOR REGULAR CHARTS: SHOW SAMPLE DAYS
        # ========================================
        else:
            context += "\nSample Data (first 3 days):\n"
            
            # Show first 3 days
            for i, item in enumerate(data[:3]):
                context += f"\n{item.get('valid_date') or item.get('created_at')}:\n"
                for key, value in item.items():
                    if key not in ['location_id', 'model_name', 'forecast_day_id', 'created_at', 'updated_at', 'forecast_reference_time', 'valid_date']:
                        context += f"  - {key}: {value}\n"
            
            # Add statistics
            context += self._add_daily_stats(data)
        
        return context
 
    
    def _build_hourly_context(
        self,
        data: Dict[str, Any],
        chart_name: str,
        location: str
    ) -> str:
        """Build context for hourly data"""
        
        if not data or 'parameters' not in data or len(data['parameters']) == 0:
            return f"Location: {location}\nChart: {chart_name}\nNo data available"
        
        params = data['parameters']
        
        # Get time range from first parameter
        first_param_key = list(params.keys())[0]
        times = params[first_param_key].get('times', [])
        start_time = times[0] if times else 'N/A'
        end_time = times[-1] if times else 'N/A'
        
        # Build context
        context = f"""
        Location: {location}
        Chart: {chart_name}
        Period: {start_time} to {end_time}
        Hours: {len(times)}

        Parameters:
        """
        # Add parameter info
        for param_key, param_data in params.items():
            values = param_data.get('values', [])
            if values:
                context += f"\n{param_data.get('name', param_key)} ({param_data.get('unit', '')}):\n"
                context += f"  - Current: {values[0]}\n"
                context += f"  - Max: {max(values)}\n"
                context += f"  - Min: {min(values)}\n"
                context += f"  - Avg: {sum(values)/len(values):.2f}\n"
        
        return context
    
    def _add_daily_stats(self, data: List[Dict[str, Any]]) -> str:
        """Add statistical summary for daily data (non-climate charts)"""
        
        stats = "\nStatistical Summary:\n"
        
        # Get all numeric fields
        numeric_fields = {}
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)) and key not in ['location_id', 'model_id', 'forecast_day_id']:
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)
        
        # Limit to 5 fields
        max_fields = 5
        field_count = 0
        
        # Calculate stats
        for field, values in numeric_fields.items():
            if values and field_count < max_fields:
                stats += f"  {field}: Max={max(values):.2f}, Min={min(values):.2f}, Avg={sum(values)/len(values):.2f}\n"
                field_count += 1
        
        if len(numeric_fields) > max_fields:
            stats += f"  ... and {len(numeric_fields) - max_fields} more fields\n"
        
        return stats
    
    
    def _add_daily_stats_compact(self, data: List[Dict[str, Any]]) -> str:
        """Add ultra-compact statistical summary (for climate charts)"""
        
        stats = ""
        
        # Get all numeric fields
        numeric_fields = {}
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)) and key not in ['location_id', 'model_id', 'forecast_day_id']:
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)
        
        # Limit to 3 most important fields
        max_fields = 3
        field_count = 0
        
        # Calculate stats (one line per field)
        for field, values in numeric_fields.items():
            if values and field_count < max_fields:
                max_val = max(values)
                min_val = min(values)
                avg_val = sum(values) / len(values)
                stats += f"  {field}: {min_val:.1f} → {max_val:.1f} (avg: {avg_val:.1f})\n"
                field_count += 1
        
        if len(numeric_fields) > max_fields:
            stats += f"  ... +{len(numeric_fields) - max_fields} more parameters\n"
        
        return stats

    def _add_climate_trends(self, data: List[Dict[str, Any]]) -> str:
        """Add simple trend analysis for climate data"""
        
        if len(data) < 2:
            return "  Insufficient data for trend analysis\n"
        
        trends = ""
        
        # Get numeric fields
        numeric_fields = {}
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)) and key not in ['location_id', 'model_id', 'forecast_day_id']:
                    if key not in numeric_fields:
                        numeric_fields[key] = []
                    numeric_fields[key].append(value)
        
        # Analyze first field only (usually temperature)
        first_field = list(numeric_fields.keys())[0] if numeric_fields else None
        
        if first_field:
            values = numeric_fields[first_field]
            first_val = values[0]
            last_val = values[-1]
            change = last_val - first_val
            
            if abs(change) < 0.5:
                trend_dir = "stable"
            elif change > 0:
                trend_dir = "increasing"
            else:
                trend_dir = "decreasing"
            
            trends += f"  {first_field}: {trend_dir} ({first_val:.1f} → {last_val:.1f}, change: {change:+.1f})\n"
        
        return trends
    
    def chat(
        self,
        user_id: int,
        query_text: str,
        location_id: Optional[int] = None,
        chart_type: Optional[str] = None,
        chart_id: Optional[str] = None,
        chart_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query with AI and return response
        
        Args:
            user_id: User ID making the query
            query_text: The question/query from user
            location_id: Location context for the query
            chart_type: Type of chart context (weather_daily, marine_hourly, etc.)
            chart_data: Actual data from the chart
            session_id: Session identifier for conversation tracking
            
        Returns:
            Dict with AI response and metadata
        """
        start_time = time.time()
        
        try:
            # Get location name if provided
            location_name = None
            if location_id:
                try:
                   location = self.location_service.get_location_by_id(location_id)
                   if location:
                       location_name = f"{location.get('name', 'Unknown')}, {location.get('country_name', 'Unknown')}"
                except Exception as e:
                    self.logger.warning(f"Failed to get location name: {str(e)}")
                    location_name = "Unknown Location"
                    
                print(f"📥 Processing query:")
                print(f"  User ID: {user_id}")
                print(f"  Query: {query_text[:50]}...")
                print(f"  Chart Type: {chart_type}")
                print(f"  Chart ID: {chart_id}")
                print(f"  Data Type: {type(chart_data).__name__}")
                        
            # Build context from chart data
            context = self._build_context(
                chart_type=chart_type,
                chart_id=chart_id,
                chart_data=chart_data,
                location_name=location_name
            )
            
            context_size = len(context)
            print(f"Context size: {context_size} characters")
        
            if context_size > 8000:
                print(f"⚠️  Large context detected: {context_size} chars")
            
            print(f"Context preview:\n{context[:500]}...")
            
            # Detect intent and extract entities
            intent = self._detect_intent(query_text, chart_type)
            entities = self._extract_entities(query_text)
            
            print(f"Intent: {intent}")
            print(f" Entities: {entities}")
            
            # Generate AI response
            prompt = self._build_prompt(
                query_text=query_text,
                context=context,
                chart_id=chart_id
            )
            
            prompt_size = len(prompt)
            print(f"Prompt size: {prompt_size} characters")
            
            try:
                print("🤖 Calling Gemini API...")
                response = self.model.generate_content(prompt)

                if not response or not response.text or response.text.strip() == "":
                    raise ValueError("Gemini returned empty response. Context may be too large.")
                
                response_text = response.text.strip()
            
            except Exception as gemini_error:
                self.logger.error(f"Gemini API error: {str(gemini_error)}")
                raise ValueError(f"AI model error: {str(gemini_error)}")
            
            # Count tokens (approximate)
            tokens_used = len(prompt.split()) + len(response_text.split())
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Save query to database
            query_id = self._save_query(
                user_id=user_id,
                location_id=location_id,
                query_text=query_text,
                intent_detected=intent,
                entities_extracted=entities,
                response_text=response_text,
                response_data={'chart_type': chart_type, 'chart_id':chart_id},
                processing_time_ms=processing_time_ms,
                tokens_used=tokens_used,
                session_id=session_id
            )
            
            return {
                'success': True,
                'query_id': query_id,
                'response': response_text,
                'intent': intent,
                'entities': entities,
                'location': location_name,
                'chart_name': self.chart_filters.get(chart_id, {}).get('name', chart_type),
                'processing_time_ms': processing_time_ms,
                'tokens_used': tokens_used,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Save failed query
            try:
                self._save_query(
                    user_id=user_id,
                    location_id=location_id,
                    query_text=query_text,
                    response_text=f"Error: {str(e)}",
                    processing_time_ms=processing_time_ms,
                    session_id=session_id
                )
            except Exception as save_error:
                self.logger.error(f"Failed to save error query: {str(save_error)}")
            
            raise HTTPException(
                status_code=500,
                detail=f"AI service error: {str(e)}"
            )
    
    def _build_prompt(
        self,
        query_text: str,
        context: str,
        chart_id: Optional[str] = None
    ) -> str:
        """Build the complete prompt for Gemini"""
        
        chart_name = self.chart_filters.get(chart_id, {}).get('name', 'general') if chart_id else 'general'
        is_climate = 'climate' in chart_name.lower() if chart_name else False
        prompt = f"""You are a helpful weather and climate data assistant integrated into a weather dashboard.

        
        CHART CONTEXT: {chart_name}
        CONTEXT:
        {context}

        USER QUESTION:
        {query_text}

        INSTRUCTIONS:
        1. Answer based on the provided context data
        2. Be concise and clear (2-6 sentences)
        3. Use specific numbers from the data when relevant
        4. {"Analyze the overall trend from start to end of the period" if is_climate else "If asked about trends, analyze the data provided"}
        5. If the question is outside the context, politely explain what data you have
        6. Use appropriate weather terminology
        7. Format numbers with appropriate units (°C, mm, m, km/h, etc.)
        8. If giving recommendations, base them on the data
        9. Use emojis sparingly (🌡️ ☀️ 🌧️ 💨 📈 📉)


        IMPORTANT:
        - DO NOT make up data or values
        - DO NOT reference data from outside this context
        - If you cannot answer from the given data, say so clearly
        - Keep responses short and actionable
        
        Respond in a friendly, professional tone suitable for a weather dashboard, also you can answer questions about climate, weather, air quality, satellite
        radiation, marine, etc.
        If you are asked about a topic unrelated to the weather, avoid the question and redirect it to the weather. If the user ask you in other language
        give to the user a answer in that language. 
        """
        return prompt
    
    def _detect_intent(self, query_text: str, chart_type: Optional[str]) -> str:
        """Detect the intent of the user query (English & Spanish)"""
        
        query_lower = query_text.lower()
        
        # Intent patterns (English & Spanish)
        if any(word in query_lower for word in [
            # English
            'when', 'what time', 'which day',
            # Spanish
            'cuándo', 'cuando', 'qué hora', 'que hora', 'qué día', 'que dia'
        ]):
            return 'temporal_query'
        
        elif any(word in query_lower for word in [
            # English
            'highest', 'maximum', 'max', 'peak', 'most',
            # Spanish
            'más alto', 'mas alto', 'máximo', 'maximo', 'pico', 'mayor', 'más', 'mas'
        ]):
            return 'find_maximum'
        
        elif any(word in query_lower for word in [
            # English
            'lowest', 'minimum', 'min', 'least',
            # Spanish
            'más bajo', 'mas bajo', 'mínimo', 'minimo', 'menor', 'menos'
        ]):
            return 'find_minimum'
        
        elif any(word in query_lower for word in [
            # English
            'average', 'mean', 'typical',
            # Spanish
            'promedio', 'media', 'típico', 'tipico', 'normal'
        ]):
            return 'calculate_average'
        
        elif any(word in query_lower for word in [
            # English
            'trend', 'pattern', 'change', 'increasing', 'decreasing',
            # Spanish
            'tendencia', 'patrón', 'patron', 'cambio', 'aumentando', 'disminuyendo',
            'subiendo', 'bajando', 'incrementando', 'reduciendo'
        ]):
            return 'analyze_trend'
        
        elif any(word in query_lower for word in [
            # English
            'compare', 'difference', 'vs', 'versus',
            # Spanish
            'comparar', 'diferencia', 'comparación', 'comparacion', 'versus'
        ]):
            return 'comparison'
        
        elif any(word in query_lower for word in [
            # English
            'recommend', 'suggest', 'should', 'best',
            # Spanish
            'recomienda', 'sugerir', 'debería', 'deberia', 'mejor', 'conviene'
        ]):
            return 'recommendation'
        
        elif any(word in query_lower for word in [
            # English
            'why', 'how', 'explain', 'what',
            # Spanish
            'por qué', 'por que', 'porqué', 'porque', 'cómo', 'como', 
            'explica', 'explicar', 'qué', 'que'
        ]):
            return 'explanation'
        
        elif any(word in query_lower for word in [
            # English
            'summary', 'overview', 'describe',
            # Spanish
            'resumen', 'descripción', 'descripcion', 'describir', 'general'
        ]):
            return 'summary'
        
        else:
            return 'general_inquiry'
        
    def _extract_entities(
        self,
        query_text: str
    ) -> Dict[str, Any]:
        """Extract entities from the query (English & Spanish)"""
        
        entities = {}
        query_lower = query_text.lower()
        
        # ========================================
        # TEMPORAL ENTITIES (English & Spanish)
        # ========================================
        temporal_terms = [
            # English
            'today', 'tomorrow', 'tonight', 'morning', 'afternoon', 'evening', 
            'week', 'weekend', 'yesterday', 'next week', 'this week',
            # Spanish
            'hoy', 'mañana', 'esta noche', 'noche', 'tarde', 'día', 'dia',
            'semana', 'fin de semana', 'ayer', 'próxima semana', 'proxima semana',
            'esta semana'
        ]
        for term in temporal_terms:
            if term in query_lower:
                entities['temporal'] = term
                break
        
        # ========================================
        # WEATHER PARAMETERS (English & Spanish)
        # ========================================
        weather_params = [
            # English
            'temperature', 'rain', 'precipitation', 'wind', 'humidity', 
            'pressure', 'cloud', 'uv', 'snow', 'storm', 'weather',
            # Spanish
            'temperatura', 'lluvia', 'precipitación', 'precipitacion', 
            'viento', 'humedad', 'presión', 'presion', 'nube', 'nubes',
            'nieve', 'tormenta', 'clima', 'tiempo'
        ]
        mentioned_params = [param for param in weather_params if param in query_lower]
        if mentioned_params:
            entities['parameters'] = mentioned_params
        
        # ========================================
        # MARINE PARAMETERS (English & Spanish)
        # ========================================
        marine_params = [
            # English
            'wave', 'waves', 'swell', 'tide', 'current', 'sea temperature', 
            'ocean', 'surf', 'surfing', 'marine',
            # Spanish
            'ola', 'olas', 'oleaje', 'marea', 'corriente', 'temperatura del mar',
            'océano', 'oceano', 'mar', 'surf', 'surfear', 'marino', 'marítimo', 'maritimo'
        ]
        mentioned_marine = [param for param in marine_params if param in query_lower]
        if mentioned_marine:
            entities['marine_parameters'] = mentioned_marine
        
        # ========================================
        # AIR QUALITY PARAMETERS (English & Spanish)
        # ========================================
        aq_params = [
            # English
            'aqi', 'pm2.5', 'pm10', 'ozone', 'pollution', 'air quality',
            'particulate matter', 'smog',
            # Spanish
            'calidad del aire', 'contaminación', 'contaminacion', 
            'material particulado', 'ozono', 'smog', 'partículas', 'particulas'
        ]
        mentioned_aq = [param for param in aq_params if param in query_lower]
        if mentioned_aq:
            entities['air_quality_parameters'] = mentioned_aq
        
        # ========================================
        # SATELLITE RADIATION (English & Spanish)
        # ========================================
        satellite_params = [
            # English
            'solar', 'radiation', 'irradiance', 'shortwave', 'dni', 
            'direct normal irradiance', 'ghi', 'global horizontal irradiance',
            'satellite', 'solar energy', 'solar power', 'sun',
            # Spanish
            'solar', 'radiación', 'radiacion', 'irradiancia', 'onda corta',
            'irradiancia normal directa', 'irradiancia horizontal global',
            'satélite', 'satelite', 'energía solar', 'energia solar',
            'potencia solar', 'sol'
        ]
        mentioned_satellite = [param for param in satellite_params if param in query_lower]
        if mentioned_satellite:
            entities['satellite_parameters'] = mentioned_satellite
        
        # ========================================
        # CLIMATE CHANGE (English & Spanish)
        # ========================================
        climate_params = [
            # English
            'climate', 'climate change', 'global warming', 'projection',
            'forecast', 'long-term', 'future', 'trend', 'warming', 'cooling',
            'climate model', 'scenario',
            # Spanish
            'clima', 'cambio climático', 'cambio climatico', 'calentamiento global',
            'proyección', 'proyeccion', 'pronóstico', 'pronostico',
            'largo plazo', 'futuro', 'tendencia', 'calentamiento', 'enfriamiento',
            'modelo climático', 'modelo climatico', 'escenario'
        ]
        mentioned_climate = [param for param in climate_params if param in query_lower]
        if mentioned_climate:
            entities['climate_parameters'] = mentioned_climate
        
        return entities
    
    # Database Operations
    
    def _save_query(
        self,
        user_id: int,
        query_text: str,
        response_text: str,
        location_id: Optional[int] = None,
        intent_detected: Optional[str] = None,
        entities_extracted: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        session_id: Optional[str] = None,
        satisfaction_rating: Optional[int] = None
    ) -> int:
        """Save query to user_queries table"""
        
        query = """
            INSERT INTO user_queries (
                user_id, location_id, query_text, query_type, intent_detected,
                entities_extracted, response_text, response_data,
                satisfaction_rating, processing_time_ms, api_calls_made,
                tokens_used, created_at, session_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s
            )
        """
        
        params = (
            user_id,
            location_id,
            query_text,
            'ai_chat',
            intent_detected,
            json.dumps(entities_extracted) if entities_extracted else None,
            response_text,
            json.dumps(response_data) if response_data else None,
            satisfaction_rating,
            processing_time_ms,
            1,  # API call to Gemini
            tokens_used,
            session_id
        )
        
        try:
            query_id = self.db.execute_insert(query, params)
            
            if query_id and query_id != -1:
                self.logger.info(f"✓ Query saved with ID: {query_id}")
                return query_id
            else:
                self.logger.error("Failed to save query: execute_insert returned -1")
                return None
        except Exception as e:
            self.logger.error(f"Error saving query: {str(e)}", exc_info=True)
            return None
        
    
    def rate_response(self, query_id: int, rating: int) -> bool:
        """
        Update satisfaction rating for a query
        
        Args:
            query_id: The query ID to rate
            rating: Rating from 1-5
            
        Returns:
            True if successful
        """
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        query = """
            UPDATE user_queries
            SET satisfaction_rating = %s
            WHERE query_id = %s
        """
        
        self.db.execute_update(query, (rating, query_id))
        return True
    
    def get_query_history(
        self,
        user_id: int,
        limit: int = 20,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get query history for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of queries to return
            session_id: Optional session filter
            
        Returns:
            List of query records
        """
        if session_id:
            query = """
                SELECT * FROM user_queries
                WHERE user_id = %s AND session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (user_id, session_id, limit)
        else:
            query = """
                SELECT * FROM user_queries
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (user_id, limit)
        
        results = self.db.execute_query(query, params)
        
        # Parse JSON fields
        for result in results:
            if result.get('entities_extracted'):
                result['entities_extracted'] = json.loads(result['entities_extracted'])
            if result.get('response_data'):
                result['response_data'] = json.loads(result['response_data'])
        
        return results
    
    def get_query_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about user queries"""
        
        query = """
            SELECT 
                COUNT(*) as total_queries,
                AVG(satisfaction_rating) as avg_rating,
                AVG(processing_time_ms) as avg_processing_time,
                SUM(tokens_used) as total_tokens,
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(DISTINCT location_id) as locations_queried
            FROM user_queries
            WHERE user_id = %s
        """
        
        result = self.db.execute_query(query, (user_id,))
        return result[0] if result else {}