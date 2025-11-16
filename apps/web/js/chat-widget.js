/**
 * DataViento - AI Chat Widget
 * 
 * Floating chat interface with context-aware AI assistant
 */

console.log("chat-widget.js loaded");

import { weatherStore } from "./dashboard.js";

import { activeLocationId } from "./dashboard.js";
// ========================================
// CHAT STATE
// ========================================

const chatState = {
    isOpen: false,
    currentContext: null,
    sessionId: null,
    messages: [],
    isTyping: false,
    isDragging: false,
    dragStartTime: 0
};

// ========================================
// CONTEXT MAPPING (Based on actual charts from weather-charts.js)
// ========================================

const CHART_CONTEXTS = {
    // ========================================
    // WEATHER FORECAST
    // ========================================
    'weather-daily-temp': {
        name: '🌡️ Weather Daily Temperature',
        dataKey: 'dailyWeatherData',
        chartType: 'weather_daily',
        chartId: 'weatherTempChart',
        suggestions: [
            "What's the coldest day this week?",
            "Show me temperature trends",
            "Which day has the highest temperature?"
        ]
    },
    'weather-daily-precip': {
        name: '🌧️ Weather Daily Precipitation',
        dataKey: 'dailyWeatherData',
        chartType: 'weather_daily',
        chartId: 'weatherPrecipChart',
        suggestions: [
            "When will it rain?",
            "How much rain is expected?",
            "Which day has the most precipitation?"
        ]
    },
    'weather-daily-wind': {
        name: '💨 Weather Daily Wind',
        dataKey: 'dailyWeatherData',
        chartType: 'weather_daily',
        chartId: 'weatherWindChart',
        suggestions: [
            "When will be the windiest day?",
            "Show wind speed trends",
            "Are there strong gusts expected?"
        ]
    },
    'weather-daily-uv': {
        name: '☀️ Weather UV & Sunshine',
        dataKey: 'dailyWeatherData',
        chartType: 'weather_daily',
        chartId: 'weatherUvChart',
        suggestions: [
            "When is UV index highest?",
            "How much sunshine today?",
            "Is it safe to be outside?"
        ]
    },
    'weather-hourly-temp': {
        name: '🌡️ Weather Hourly Temperature',
        dataKey: 'hourlyWeatherData',
        chartType: 'weather_hourly',
        chartId: 'weatherHourlyTempChart',
        suggestions: [
            "What time will be hottest?",
            "Show temperature and humidity",
            "When will temperature drop?"
        ]
    },
    'weather-hourly-precip': {
        name: '🌧️ Weather Hourly Precipitation',
        dataKey: 'hourlyWeatherData',
        chartType: 'weather_hourly',
        chartId: 'weatherHourlyPrecipChart',
        suggestions: [
            "Will it rain today?",
            "What time will it rain?",
            "Show precipitation probability"
        ]
    },
    'weather-hourly-wind': {
        name: '💨 Weather Hourly Wind',
        dataKey: 'hourlyWeatherData',
        chartType: 'weather_hourly',
        chartId: 'weatherHourlyWindChart',
        suggestions: [
            "When is wind speed highest?",
            "Show wind direction",
            "Is it windy this afternoon?"
        ]
    },

    // ========================================
    // AIR QUALITY
    // ========================================
    'air-quality-aqi': {
        name: '🌫️ Air Quality Index',
        dataKey: 'hourlyAirQualityData',
        chartType: 'air_quality',
        chartId: 'airQualityAqiChart',
        suggestions: [
            "Is it safe to go for a run?",
            "What's the AQI level?",
            "When is air quality best?"
        ]
    },
    'air-quality-pollutants': {
        name: '💨 Air Quality Pollutants',
        dataKey: 'hourlyAirQualityData',
        chartType: 'air_quality',
        chartId: 'airQualityPollutantsChart',
        suggestions: [
            "What are PM2.5 levels?",
            "Show ozone trends",
            "Are pollution levels high?"
        ]
    },
    'air-quality-secondary': {
        name: '🏭 Secondary Pollutants',
        dataKey: 'hourlyAirQualityData',
        chartType: 'air_quality',
        chartId: 'airQualitySecondaryChart',
        suggestions: [
            "What are SO2 levels?",
            "Show CO trends",
            "Are secondary pollutants high?"
        ]
    },

    // ========================================
    // MARINE FORECAST
    // ========================================
    'marine-daily-wave': {
        name: '🌊 Marine Daily Wave Heights',
        dataKey: 'dailyMarineData',
        chartType: 'marine_daily',
        chartId: 'marineDailyWaveChart',
        suggestions: [
            "Is it safe to surf tomorrow?",
            "What's the max wave height?",
            "Show wave trends"
        ]
    },
    'marine-daily-period': {
        name: '🌀 Marine Daily Wave Period',
        dataKey: 'dailyMarineData',
        chartType: 'marine_daily',
        chartId: 'marineDailyPeriodChart',
        suggestions: [
            "What's the wave period?",
            "Show wave direction",
            "Are waves smooth or choppy?"
        ]
    },
    'marine-hourly-wave': {
        name: '🌊 Marine Hourly Wave Heights',
        dataKey: 'hourlyMarineData',
        chartType: 'marine_hourly',
        chartId: 'marineHourlyWaveChart',
        suggestions: [
            "What time are waves highest?",
            "Show swell vs wind waves",
            "Wave conditions now?"
        ]
    },
    'marine-hourly-period': {
        name: '🌡️ Marine Hourly Period & Temp',
        dataKey: 'hourlyMarineData',
        chartType: 'marine_hourly',
        chartId: 'marineHourlyPeriodChart',
        suggestions: [
            "Sea temperature now?",
            "Wave period trends",
            "Is water temperature comfortable?"
        ]
    },

    // ========================================
    // SATELLITE RADIATION
    // ========================================
    'satellite-radiation': {
        name: '☀️ Solar Radiation Components',
        dataKey: 'dailySatelliteData',
        chartType: 'satellite',
        chartId: 'satelliteDailyRadiationChart',
        suggestions: [
            "Best time for solar energy?",
            "Show radiation trends",
            "Compare shortwave vs direct"
        ]
    },
    'satellite-irradiance': {
        name: '🌞 Solar Irradiance (DNI/GHI)',
        dataKey: 'dailySatelliteData',
        chartType: 'satellite',
        chartId: 'satelliteDailyIrradianceChart',
        suggestions: [
            "What's the DNI value?",
            "Compare DNI vs GTI",
            "Solar panel efficiency?"
        ]
    },

    // ========================================
    // CLIMATE PROJECTIONS
    // ========================================
    'climate-temp': {
        name: '🌍 Climate Temperature Trends',
        dataKey: 'climateProjectionData',
        chartType: 'climate',
        chartId: 'climateTempTrendsChart',
        suggestions: [
            "Is temperature increasing?",
            "Show 5-year trends",
            "Climate change patterns?"
        ]
    },
    'climate-precip': {
        name: '🌧️ Climate Precipitation & Humidity',
        dataKey: 'climateProjectionData',
        chartType: 'climate',
        chartId: 'climatePrecipHumidityChart',
        suggestions: [
            "Precipitation patterns?",
            "Show humidity trends",
            "Is rainfall increasing?"
        ]
    },
    'climate-wind': {
        name: '💨 Climate Wind & Radiation',
        dataKey: 'climateProjectionData',
        chartType: 'climate',
        chartId: 'climateWindRadiationChart',
        suggestions: [
            "Wind speed trends?",
            "Solar radiation patterns?",
            "Long-term climate changes?"
        ]
    }
};

// ========================================
// INITIALIZATION
// ========================================

function initializeChatWidget() {
    console.log("🤖 Initializing AI Chat Widget...");
    console.log('Data Sample:', weatherStore.currentWeatherData);
    
    // Generate session ID
    chatState.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Create chat elements
    createChatHead();
    createChatContainer();
    
    // Detect active context
    detectActiveContext();
    
    // Set up event listeners
    setupChatEvents();
    
    console.log("✅ Chat Widget initialized");
}

function createChatHead() {
    const chatHead = document.createElement('div');
    chatHead.className = 'chat-head';
    chatHead.id = 'chatHead';
    chatHead.innerHTML = `
        <div class="chat-head-icon">🤖</div>
    `;
    
    document.body.appendChild(chatHead);
    
    // Make draggable
    makeDraggable(chatHead);
}

function createChatContainer() {
    const chatContainer = document.createElement('div');
    chatContainer.className = 'chat-container';
    chatContainer.id = 'chatContainer';
    
    chatContainer.innerHTML = `
        <!-- Header -->
        <div class="chat-header">
            <div class="chat-header-left">
                <div class="chat-header-avatar">🤖</div>
                <div class="chat-header-info">
                    <h3>DataViento AI</h3>
                    <p>Weather Assistant</p>
                </div>
            </div>
            <div class="chat-header-actions">
                <button class="chat-header-btn" id="chatMinimizeBtn" title="Minimize">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M4 8a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 8z"/>
                    </svg>
                </button>
            </div>
        </div>
        
        <!-- Context Selector -->
        <div class="chat-context">
            <span class="chat-context-label">📊 Chart:</span>
            <select id="chatContextSelect" class="chat-context-select">
                <option value="">-- Select a chart --</option>
                <optgroup label="🌤️ Weather Forecast">
                    ${Object.entries(CHART_CONTEXTS)
                        .filter(([key]) => key.startsWith('weather-'))
                        .map(([key, ctx]) => `<option value="${key}">${ctx.name}</option>`)
                        .join('')}
                </optgroup>
                <optgroup label="🌫️ Air Quality">
                    ${Object.entries(CHART_CONTEXTS)
                        .filter(([key]) => key.startsWith('air-quality-'))
                        .map(([key, ctx]) => `<option value="${key}">${ctx.name}</option>`)
                        .join('')}
                </optgroup>
                <optgroup label="🌊 Marine Weather">
                    ${Object.entries(CHART_CONTEXTS)
                        .filter(([key]) => key.startsWith('marine-'))
                        .map(([key, ctx]) => `<option value="${key}">${ctx.name}</option>`)
                        .join('')}
                </optgroup>
                <optgroup label="🛰️ Satellite">
                    ${Object.entries(CHART_CONTEXTS)
                        .filter(([key]) => key.startsWith('satellite-'))
                        .map(([key, ctx]) => `<option value="${key}">${ctx.name}</option>`)
                        .join('')}
                </optgroup>
                <optgroup label="🌍 Climate">
                    ${Object.entries(CHART_CONTEXTS)
                        .filter(([key]) => key.startsWith('climate-'))
                        .map(([key, ctx]) => `<option value="${key}">${ctx.name}</option>`)
                        .join('')}
                </optgroup>
            </select>
        </div>
        
        <!-- Messages -->
        <div class="chat-messages" id="chatMessages">
            <!-- Welcome message will be inserted here -->
        </div>
        
        <!-- Suggestions (shown when empty) -->
        <div class="chat-suggestions" id="chatSuggestions"></div>
        
        <!-- Input -->
        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <textarea 
                    id="chatInput" 
                    class="chat-input" 
                    placeholder="Ask me about the weather data..."
                    rows="1"
                ></textarea>
                <button id="chatSendBtn" class="chat-send-btn">
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M15.854.146a.5.5 0 0 1 .11.54l-5.819 14.547a.75.75 0 0 1-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 0 1 .124-1.33L15.314.037a.5.5 0 0 1 .54.11ZM6.636 10.07l2.761 4.338L14.13 2.576 6.636 10.07Zm6.787-8.201L1.591 6.602l4.339 2.76 7.494-7.493Z"/>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(chatContainer);
    
    // Show welcome message
    showWelcomeMessage();
}

// ========================================
// DRAGGABLE CHAT HEAD (FIX: Drag vs Click)
// ========================================

function makeDraggable(element) {
    let startX, startY, startLeft, startTop;
    let hasMoved = false;
    
    element.addEventListener('mousedown', (e) => {
        // Record start time and position
        chatState.dragStartTime = Date.now();
        hasMoved = false;
        
        startX = e.clientX;
        startY = e.clientY;
        startLeft = element.offsetLeft;
        startTop = element.offsetTop;
        
        element.style.transition = 'none';
        document.body.style.userSelect = 'none';
        element.style.cursor = 'grabbing';
        
        // Add move and up listeners to document
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
    
    function onMouseMove(e) {
        e.preventDefault();
        
        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;
        
        // Consider it a drag if moved more than 5px
        if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
            hasMoved = true;
            chatState.isDragging = true;
        }
        
        if (hasMoved) {
            let newLeft = startLeft + deltaX;
            let newTop = startTop + deltaY;
            
            // Keep within viewport
            const maxLeft = window.innerWidth - element.offsetWidth;
            const maxTop = window.innerHeight - element.offsetHeight;
            
            newLeft = Math.max(0, Math.min(newLeft, maxLeft));
            newTop = Math.max(0, Math.min(newTop, maxTop));
            
            element.style.left = newLeft + 'px';
            element.style.top = newTop + 'px';
            element.style.right = 'auto';
            element.style.bottom = 'auto';
        }
    }
    
    function onMouseUp(e) {
        element.style.transition = '';
        document.body.style.userSelect = '';
        element.style.cursor = 'move';
        
        // Remove listeners
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        
        // If it was a click (not a drag), toggle chat
        const clickDuration = Date.now() - chatState.dragStartTime;
        
        if (!hasMoved && clickDuration < 300) {
            // It was a click!
            toggleChat();
        }
        
        // Reset state
        chatState.isDragging = false;
        hasMoved = false;
    }
}

// ========================================
// CHAT ACTIONS
// ========================================

function toggleChat() {
    const container = document.getElementById('chatContainer');
    chatState.isOpen = !chatState.isOpen;
    
    if (chatState.isOpen) {
        container.classList.add('active');
        document.getElementById('chatInput').focus();
    } else {
        container.classList.remove('active');
    }
}

function setupChatEvents() {
    // Minimize button
    document.getElementById('chatMinimizeBtn').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleChat();
    });
    
    // Context change
    document.getElementById('chatContextSelect').addEventListener('change', handleContextChange);
    
    // Send message
    document.getElementById('chatSendBtn').addEventListener('click', sendMessage);
    
    // Enter to send (Shift+Enter for new line)
    document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    document.getElementById('chatInput').addEventListener('input', (e) => {
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
    });
}

function handleContextChange(e) {
    const contextKey = e.target.value;
    
    if (!contextKey) {
        chatState.currentContext = null;
        hideSuggestions();
        return;
    }
    
    chatState.currentContext = contextKey;
    console.log(`📊 Context changed to: ${CHART_CONTEXTS[contextKey].name}`);
    
    // Show suggestions
    showSuggestions(contextKey);
}

// ========================================
// DETECT ACTIVE CONTEXT
// ========================================

function detectActiveContext() {
    // Try to detect based on visible charts
    const visibleCharts = Object.keys(CHART_CONTEXTS).filter(key => {
        const chartId = CHART_CONTEXTS[key].chartId;
        const chartElement = document.getElementById(chartId);
        return chartElement && chartElement.offsetParent !== null; // Check if visible
    });
    
    if (visibleCharts.length > 0) {
        // Use first visible chart
        const contextKey = visibleCharts[0];
        chatState.currentContext = contextKey;
        document.getElementById('chatContextSelect').value = contextKey;
        console.log(`🎯 Auto-detected context: ${CHART_CONTEXTS[contextKey].name}`);
        showSuggestions(contextKey);
    }
}

// Listen for section changes
document.addEventListener('DOMContentLoaded', () => {
    const sidebarItems = document.querySelectorAll('.sidebar-item');
    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            setTimeout(detectActiveContext, 500); // Wait for section to load
        });
    });
});

// ========================================
// MESSAGES
// ========================================

function showWelcomeMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-message-icon">🤖</div>
            <h3>Hi! I'm DataViento AI</h3>
            <p>
                I can help you understand your weather data, answer questions about forecasts,
                and provide insights from the charts.
            </p>
            <p style="margin-top: 1rem; font-size: 13px; color: #94a3b8;">
                💡 Select a chart above to get started!
            </p>
        </div>
    `;
}

function addMessage(content, type = 'ai', metadata = {}) {
    const messagesContainer = document.getElementById('chatMessages');
    
    // Remove welcome message if exists
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    let ratingHtml = '';
    if (type === 'ai' && metadata.queryId) {
        ratingHtml = `
            <div class="message-rating">
                <span class="rating-label">Rate:</span>
                <button class="rating-btn" data-rating="1" data-query-id="${metadata.queryId}">👎</button>
                <button class="rating-btn" data-rating="5" data-query-id="${metadata.queryId}">👍</button>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar ${type}">
            ${type === 'ai' ? '🤖' : '👤'}
        </div>
        <div class="message-content">
            <div class="message-bubble">${content}</div>
            <div class="message-metadata">
                <span class="message-time">${timestamp}</span>
                ${metadata.processingTime ? `<span>• ${metadata.processingTime}ms</span>` : ''}
            </div>
            ${ratingHtml}
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    
    // Add rating listeners
    if (type === 'ai' && metadata.queryId) {
        messageDiv.querySelectorAll('.rating-btn').forEach(btn => {
            btn.addEventListener('click', () => rateResponse(btn));
        });
    }
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Store in state
    chatState.messages.push({
        type,
        content,
        timestamp: new Date(),
        metadata
    });
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message ai';
    typingDiv.id = 'typingIndicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar ai">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    chatState.isTyping = true;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    chatState.isTyping = false;
}

// ========================================
// SEND MESSAGE
// ========================================

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const query = input.value.trim();
    
    if (!query) return;
    
    // Add user message
    addMessage(query, 'user');
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Show typing
    showTypingIndicator();
    
    let chartData = null;
    let chartId = null;
    let chartType = 'general';

    if(chatState.currentContext)
    {
         // Get chart data
        const context = CHART_CONTEXTS[chatState.currentContext];
        console.log('Selected Context:', context);
        const dataKey = context.dataKey;
        chartData = weatherStore[dataKey];
        chartType = context.chartType;
        chartId = context.chartId;
        
        console.log('Data Key:', dataKey);
        console.log('Chart Data:', chartData);
        console.log('Chart Type:', chartType);
        console.log('Chart ID:', chartId);

        if (!chartData) {
        hideTypingIndicator();
        addMessage('❌ No data loaded for this chart. Please wait for data to load.', 'ai');
        return;
    }
    }
    else
    {
        console.log('💬 General question mode (no chart context)');
        console.log('📝 Query:', query);
    }

    
    try {
        // Get user ID from active location
        const userLoc = userLocations?.find(ul => ul.user_location_id === activeLocationId);
        const userId = userLoc?.user_id || 1; // Fallback to 1 if not found
        const locationId = userLoc?.location_id || activeLocationId;
        
        console.log('UserLoc:', userLoc.location_id);
        const requestBody = {
            query:query,
            location_id:locationId,
            chart_type: chartType,
            chart_data: chartData,
            chart_id: chartId,
            session_id: chatState.sessionId
        }
        
        console.log('Request Body:', requestBody);
        console.log('Request Size (approx):', JSON.stringify(requestBody).length, 'bytes');

        const response = await fetch(getApiUrl('/ai/chat'), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        hideTypingIndicator();

        console.log('Response Status:', response.status);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('❌ API Error:', errorData);
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('AI Response:', data);

        addMessage(data.response, 'ai', {
            queryId: data.query_id,
            processingTime: data.processing_time_ms,
            intent: data.intent,
            entities: data.entities
        });

        console.log('Response added to chat');
        console.log('Intent:', data.intent);
        console.log('Entities:', data.entities);
    
    } catch (error) {
        hideTypingIndicator();
        addMessage(`❌ Error: ${error.message}. Please try again.`, 'ai');
        console.error('Chat error:', error);
    }
}

// ========================================
// RATING
// ========================================

async function rateResponse(button) {
    const queryId = button.getAttribute('data-query-id');
    const rating = parseInt(button.getAttribute('data-rating'));
    
    try {
        const response = await fetch(getApiUrl(`/ai/rate/${queryId}`), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ rating })
        });
        
        if (response.ok) {
            // Mark as selected
            button.parentElement.querySelectorAll('.rating-btn').forEach(btn => {
                btn.classList.remove('selected');
            });
            button.classList.add('selected');
            
            console.log(`✅ Rated query ${queryId}: ${rating}/5`);
        }
        
    } catch (error) {
        console.error('Rating error:', error);
    }
}

// ========================================
// SUGGESTIONS
// ========================================

function showSuggestions(contextKey) {
    const suggestionsContainer = document.getElementById('chatSuggestions');
    const context = CHART_CONTEXTS[contextKey];
    
    if (!context || chatState.messages.length > 0) {
        suggestionsContainer.innerHTML = '';
        return;
    }
    
    suggestionsContainer.innerHTML = context.suggestions.map(suggestion => 
        `<div class="suggestion-chip" data-suggestion="${suggestion}">${suggestion}</div>`
    ).join('');
    
    // Add click handlers
    suggestionsContainer.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.getElementById('chatInput').value = chip.getAttribute('data-suggestion');
            sendMessage();
            suggestionsContainer.innerHTML = '';
        });
    });
}

function hideSuggestions() {
    document.getElementById('chatSuggestions').innerHTML = '';
}

// ========================================
// INITIALIZE ON LOAD
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for other scripts to load
    setTimeout(initializeChatWidget, 1000);
});