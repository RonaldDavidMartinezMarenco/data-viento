/**
 * DataViento - Settings Management
 * 
 * Handles:
 * - Location selection and management
 * - Unit preferences (Metric/Imperial)
 * - Notification settings
 */

console.log('✅ settings.js loaded');

// ========================================
// GLOBAL STATE
// ========================================

let availableLocations = [];  // All 10 locations from backend
let userLocations = [];        // User's favorite locations
let userPreferences = null;    // User's current preferences

// ========================================
// STEP 1: LOAD AVAILABLE LOCATIONS
// ========================================

/**
 * Fetch all available locations from backend
 * 
 * GET /locations/available
 * Returns 10 pre-configured Spanish cities
 */
async function loadAvailableLocations() {
    console.log('📍 Loading available locations...');
    
    try {
        const apiUrl = getApiUrl('/locations/available');
        console.log('   API URL:', apiUrl);
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch locations');
        }
        
        availableLocations = await response.json();
        console.log(`✅ Loaded ${availableLocations.length} locations`);
        
        // Populate dropdown
        populateLocationDropdown();
        
    } catch (error) {
        console.error('❌ Error loading locations:', error);
        alert('Failed to load locations. Please refresh the page.');
    }
}

/**
 * Populate location dropdown with available cities
 */
function populateLocationDropdown() {
    console.log('📝 Populating location dropdown...');
    
    const dropdown = document.getElementById('locationSelect');
    
    if (!dropdown) {
        console.warn('⚠️ Location dropdown not found');
        return;
    }
    
    // Clear existing options (except first placeholder)
    dropdown.innerHTML = '<option value="">-- Select a city --</option>';
    
    // Add each location as an option
    availableLocations.forEach(location => {
        const option = document.createElement('option');
        option.value = location.location_id;
        option.textContent = `${location.name} (${location.country})`;
        dropdown.appendChild(option);
    });
    
    console.log(`✅ Added ${availableLocations.length} locations to dropdown`);
}

// ========================================
// STEP 2: LOAD USER'S LOCATIONS
// ========================================

/**
 * Fetch user's current favorite locations
 * 
 * GET /users/me/locations
 * Returns array of user's saved locations
 */
async function loadUserLocations() {
    console.log('📍 Loading user locations...');
    
    try {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            throw new Error('No access token available');
        }
        
        const apiUrl = getApiUrl('/users/me/locations');
        console.log('   API URL:', apiUrl);
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch user locations');
        }
        
        userLocations = await response.json();
        console.log(`✅ Loaded ${userLocations.length} user locations`);
        
        // Display user's locations
        displayUserLocations();
        
    } catch (error) {
        console.error('❌ Error loading user locations:', error);
        displayUserLocations(); // Show empty state
    }
}

/**
 * Display user's locations in the UI
 */
function displayUserLocations() {
    console.log('📝 Displaying user locations...');
    
    const container = document.getElementById('userLocationsList');
    
    if (!container) {
        console.warn('⚠️ User locations container not found');
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Check if user has locations
    if (userLocations.length === 0) {
        container.innerHTML = '<p class="empty-text">No locations added yet. Select a city above to add it to your favorites.</p>';
        return;
    }
    
    // Display each location
    userLocations.forEach(userLoc => {
        console.log('Processing userLoc:', userLoc);
        
        // Find the full location details from availableLocations
        const location = availableLocations.find(loc => loc.location_id === userLoc.location_id);
        
        console.log('Found location:', location);
        
        if (!location) {
            console.warn('⚠️ Location not found:', userLoc.location_id);
            return;
        }
        
        // Create location item
        const locationItem = document.createElement('div');
        locationItem.className = 'location-item';
        
        // Safe access to properties with fallbacks
        const locationName = location.name || 'Unknown';
        const customName = userLoc.custom_name || location.country_name || 'Spain';
        const latitude = location.latitude ? parseFloat(location.latitude).toFixed(2) : '0.00';
        const longitude = location.longitude ? parseFloat(location.longitude).toFixed(2) : '0.00';
        const notifStatus = userLoc.notification_enabled ? 'On' : 'Off';
        
        locationItem.innerHTML = `
            <div class="location-info">
                <div class="location-name">
                    ${locationName}
                    ${userLoc.is_primary ? '<span class="location-badge badge-primary">Primary</span>' : ''}
                </div>
                <div class="location-meta">
                    ${customName} • 
                    ${latitude}°, ${longitude}° • 
                    Notifications: ${notifStatus}
                </div>
            </div>
            <div class="location-actions">
                <button class="btn btn-danger btn-sm" onclick="removeLocation(${userLoc.user_location_id})">
                    Remove
                </button>
            </div>
        `;
        
        container.appendChild(locationItem);
    });
    
    console.log(`✅ Displayed ${userLocations.length} locations`);
}

// ========================================
// STEP 3: ADD LOCATION
// ========================================

/**
 * Add a location to user's favorites
 * 
 * POST /users/me/locations
 */
async function addLocation() {
    console.log('+ Adding location...');
    
    const dropdown = document.getElementById('locationSelect');
    const customNameInput = document.getElementById('customLocationName');
    const selectedLocationId = parseInt(dropdown.value);
    
    if (!selectedLocationId) {
        alert('Please select a location first');
        return;
    }
    
    // Find the selected location details
    const location = availableLocations.find(loc => loc.location_id === selectedLocationId);
    
    if (!location) {
        alert('Invalid location selected');
        return;
    }

    const customName = customNameInput.value.trim() || location.name;
    
    console.log('   Selected city:', location.name);
    console.log('   Custom name:', customName);
    
    try {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            throw new Error('No access token available');
        }
        
        const apiUrl = getApiUrl('/users/me/locations');
        console.log('   API URL:', apiUrl);
        console.log('   Adding:', customName);
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                location_id: selectedLocationId,
                custom_name: customName,
                is_primary: userLocations.length === 0, // First location is primary
                notification_enabled: true
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to add location');
        }
        
        const newLocation = await response.json();
        console.log('✅ Location added:', newLocation);
        
        // Reset dropdown
        dropdown.value = '';
        customNameInput.value = '';
        
        // Reload user locations
        await loadUserLocations();
        
        alert(`${customName} added to your favorites!`);
        
    } catch (error) {
        console.error('❌ Error adding location:', error);
        alert(`Failed to add location: ${error.message}`);
    }
}

// ========================================
// STEP 4: REMOVE LOCATION
// ========================================

/**
 * Remove a location from user's favorites
 * 
 * DELETE /users/me/locations/{location_id}
 */
async function removeLocation(userLocationId) {
    console.log('🗑️ Removing location:', userLocationId);
    
    const confirmed = confirm('Are you sure you want to remove this location?');
    
    if (!confirmed) {
        console.log('❌ Removal cancelled');
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            throw new Error('No access token available');
        }
        
        const apiUrl = getApiUrl(`/users/me/locations/${userLocationId}`);
        console.log('   API URL:', apiUrl);
        
        const response = await fetch(apiUrl, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to remove location');
        }
        
        console.log('✅ Location removed');
        
        // Reload user locations
        await loadUserLocations();
        
        alert('Location removed successfully!');
        
    } catch (error) {
        console.error('❌ Error removing location:', error);
        alert(`Failed to remove location: ${error.message}`);
    }
}

// ========================================
// STEP 5: LOAD USER PREFERENCES
// ========================================

/**
 * Load user's current preferences
 * 
 * GET /users/me/preferences
 */
async function loadUserPreferences() {
    console.log('⚙️ Loading user preferences...');
    
    try {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            throw new Error('No access token available');
        }
        
        const apiUrl = getApiUrl('/users/me/preferences');
        console.log('   API URL:', apiUrl);
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch preferences');
        }
        
        userPreferences = await response.json();
        console.log('✅ Preferences loaded:', userPreferences);
        
        // Apply preferences to UI
        applyPreferencesToUI();
        
    } catch (error) {
        console.error('❌ Error loading preferences:', error);
    }
}

/**
 * Apply loaded preferences to UI controls
 */
function applyPreferencesToUI() {
    console.log('📝 Applying preferences to UI...');
    
    if (!userPreferences) {
        console.warn('⚠️ No preferences to apply');
        return;
    }
    
    // Temperature unit
    const tempCelsius = document.getElementById('tempCelsius');
    const tempFahrenheit = document.getElementById('tempFahrenheit');
    
    if (userPreferences.preferred_temperature_unit === 'celsius') {
        tempCelsius?.classList.add('active');
        tempFahrenheit?.classList.remove('active');
    } else {
        tempCelsius?.classList.remove('active');
        tempFahrenheit?.classList.add('active');
    }
    
    // Wind speed unit
    const windKmh = document.getElementById('windKmh');
    const windMph = document.getElementById('windMph');
    
    if (userPreferences.preferred_wind_speed_unit === 'kmh') {
        windKmh?.classList.add('active');
        windMph?.classList.remove('active');
    } else {
        windKmh?.classList.remove('active');
        windMph?.classList.add('active');
    }
    
    // Precipitation unit
    const precipMm = document.getElementById('precipMm');
    const precipInch = document.getElementById('precipInch');
    
    if (userPreferences.preferred_precipitation_unit === 'mm') {
        precipMm?.classList.add('active');
        precipInch?.classList.remove('active');
    } else {
        precipMm?.classList.remove('active');
        precipInch?.classList.add('active');
    }
    
    // Notification toggle
    const notificationToggle = document.getElementById('notificationToggle');
    if (notificationToggle) {
        notificationToggle.checked = userPreferences.notification_enabled;
    }
    
    console.log('✅ Preferences applied to UI');
}

// ========================================
// STEP 6: SETUP UI EVENT LISTENERS
// ========================================

/**
 * Setup all event listeners for settings controls
 */
function setupSettingsEventListeners() {
    console.log('🎛️ Setting up event listeners...');
    
    // Add Location button
    const addLocationBtn = document.getElementById('addLocationBtn');
    if (addLocationBtn) {
        addLocationBtn.addEventListener('click', addLocation);
        console.log('  ✓ Add Location button');
    }
    
    // Temperature unit toggles
    const tempCelsius = document.getElementById('tempCelsius');
    const tempFahrenheit = document.getElementById('tempFahrenheit');
    
    tempCelsius?.addEventListener('click', () => toggleUnit('temp', 'celsius'));
    tempFahrenheit?.addEventListener('click', () => toggleUnit('temp', 'fahrenheit'));
    
    // Wind speed unit toggles
    const windKmh = document.getElementById('windKmh');
    const windMph = document.getElementById('windMph');
    
    windKmh?.addEventListener('click', () => toggleUnit('wind', 'kmh'));
    windMph?.addEventListener('click', () => toggleUnit('wind', 'mph'));
    
    // Precipitation unit toggles
    const precipMm = document.getElementById('precipMm');
    const precipInch = document.getElementById('precipInch');
    
    precipMm?.addEventListener('click', () => toggleUnit('precip', 'mm'));
    precipInch?.addEventListener('click', () => toggleUnit('precip', 'inch'));
    
    // Save Preferences button
    const saveBtn = document.getElementById('savePreferencesBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', savePreferences);
        console.log('  ✓ Save Preferences button');
    }
    
    // Notification toggle
    const notificationToggle = document.getElementById('notificationToggle');
    if (notificationToggle) {
        notificationToggle.addEventListener('change', savePreferences);
        console.log('  ✓ Notification toggle');
    }
    
    console.log('✅ Event listeners setup complete');
}

/**
 * Toggle unit preference in UI
 */
function toggleUnit(type, value) {
    if (type === 'temp') {
        const celsius = document.getElementById('tempCelsius');
        const fahrenheit = document.getElementById('tempFahrenheit');
        
        celsius?.classList.toggle('active', value === 'celsius');
        fahrenheit?.classList.toggle('active', value === 'fahrenheit');
    } else if (type === 'wind') {
        const kmh = document.getElementById('windKmh');
        const mph = document.getElementById('windMph');
        
        kmh?.classList.toggle('active', value === 'kmh');
        mph?.classList.toggle('active', value === 'mph');
    } else if (type === 'precip') {
        const mm = document.getElementById('precipMm');
        const inch = document.getElementById('precipInch');
        
        mm?.classList.toggle('active', value === 'mm');
        inch?.classList.toggle('active', value === 'inch');
    }
}

// ========================================
// STEP 7: SAVE PREFERENCES
// ========================================

/**
 * Save user preferences to backend
 * 
 * PATCH /users/me/preferences
 */
async function savePreferences() {
    console.log('💾 Saving preferences...');
    
    try {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            throw new Error('No access token available');
        }
        
        // Get current UI values
        const tempUnit = document.getElementById('tempCelsius')?.classList.contains('active') 
            ? 'celsius' : 'fahrenheit';
        const windUnit = document.getElementById('windKmh')?.classList.contains('active') 
            ? 'kmh' : 'mph';
        const precipUnit = document.getElementById('precipMm')?.classList.contains('active') 
            ? 'mm' : 'inch';
        const notificationEnabled = document.getElementById('notificationToggle')?.checked || false;
        
        const preferences = {
            preferred_temperature_unit: tempUnit,
            preferred_wind_speed_unit: windUnit,
            preferred_precipitation_unit: precipUnit,
            notification_enabled: notificationEnabled
        };
        
        console.log('   Saving:', preferences);
        
        const apiUrl = getApiUrl('/users/me/preferences');
        
        const response = await fetch(apiUrl, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(preferences)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to save preferences');
        }
        
        userPreferences = await response.json();
        console.log('✅ Preferences saved:', userPreferences);
        
        alert('Preferences saved successfully!');
        
    } catch (error) {
        console.error('❌ Error saving preferences:', error);
        alert(`Failed to save preferences: ${error.message}`);
    }
}

// ========================================
// INITIALIZE SETTINGS
// ========================================

/**
 * Initialize all settings functionality
 * Called when dashboard loads
 */
async function initializeSettings() {
    console.log('🚀 Initializing settings...');
    
    try {
        // Load data
        await loadAvailableLocations();
        await loadUserLocations();
        await loadUserPreferences();
        
        // Setup UI
        setupSettingsEventListeners();
        
        console.log('✅ Settings initialized successfully');
        
    } catch (error) {
        console.error('❌ Error initializing settings:', error);
    }
}

// Make removeLocation available globally for onclick
window.removeLocation = removeLocation;

// Export for use in dashboard.js
window.initializeSettings = initializeSettings;