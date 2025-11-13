/**
 * DataViento - Dashboard Page Logic
 *
 * Responsibilities:
 * 1. Check if user is authenticated
 * 2. Fetch user data from backend API
 * 3. Populate dashboard with user information
 * 4. Handle logout functionality
 */

console.log("dashboard.js loaded");

// ========================================
// STEP 1: CHECK AUTHENTICATION
// ========================================

/**
 * Check if user is logged in
 *
 * Reads access_token from localStorage.
 * If not found, redirects to login page.
 *
 * Why: Protected pages need authentication
 */
function checkAuthentication() {
  console.log("🔒 Checking authentication...");

  // Try to get token from localStorage
  const token = localStorage.getItem("access_token");

  if (!token) {
    // No token = not logged in
    console.log("❌ No access token found, redirecting to login");
    window.location.href = "/login.html";
    return false;
  }

  console.log("✅ Access token found:", token.substring(0, 20) + "...");
  return true;
}

// ========================================
// STEP 2: FETCH USER DATA FROM BACKEND
// ========================================

/**
 * Fetch current user data from backend
 *
 * Makes authenticated GET request to /users/me
 *
 * How it works:
 * 1. Gets access_token from localStorage
 * 2. Sends GET request to http://localhost:8000/users/me
 * 3. Includes token in Authorization header: "Bearer eyJ..."
 * 4. Backend validates token and returns user data
 *
 * Returns: Promise that resolves to user data object
 * Throws: Error if request fails or token is invalid
 */

async function fetchUserData() {
  console.log("📡 Fetching user data from backend...");

  try {
    // Step 1: Get token from localStorage
    const token = localStorage.getItem("access_token");

    if (!token) {
      throw new Error("No access token available");
    }

    console.log("   Using token:", token.substring(0, 30) + "...");

    // Step 2: Build API URL
    // Uses getApiUrl() from auth.js
    const apiUrl = getApiUrl("/users/me");
    console.log("   API URL:", apiUrl);

    // Step 3: Make GET request with Authorization header
    console.log("Sending request...");
    const response = await fetch(apiUrl, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`, // ← JWT token here
        "Content-Type": "application/json",
      },
    });

    console.log("Response received");
    console.log("Status:", response.status, response.statusText);

    // Step 4: Check if request was successful
    if (!response.ok) {
      // Handle 401 Unauthorized (invalid/expired token)
      if (response.status === 401) {
        console.log("Token invalid or expired");
        console.log("Redirecting to login...");

        // Clear stored data
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");

        // Redirect to login
        window.location.href = "/login.html";
        return null;
      }

      // Other errors
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to fetch user data");
    }

    // Step 5: Parse JSON response
    const userData = await response.json();
    console.log("User data received:", userData);

    // Step 6: Store in localStorage for quick access
    localStorage.setItem("user", JSON.stringify(userData));
    console.log("User data stored in localStorage");

    return userData;
  } catch (error) {
    console.error("Error fetching user data:", error);
    throw error;
  }
}

// ========================================
// STEP 3: POPULATE DASHBOARD HEADER
// ========================================

/**
 * Populate header section with user info
 *
 * Updates:
 * - User avatar initials (first letter of username)
 * - User full name or username
 * - User email
 * - Welcome message with first name
 *
 * @param {Object} user - User data from backend
 *
 * How it works:
 * 1. Get DOM elements by ID
 * 2. Extract data from user object
 * 3. Update text content of each element
 */

function populateHeader(user) {
  console.log("Populating header with user info...");

  // Get DOM elements
  const userInitials = document.getElementById("userInitials");
  const userName = document.getElementById("userName");
  const userEmail = document.getElementById("userEmail");
  const welcomeName = document.getElementById("welcomeName");

  // 1. Set user initials (first letter of username, uppercase)
  if (userInitials) {
    // Get first character of username and make it uppercase
    const initials = user.username.charAt(0).toUpperCase();
    userInitials.textContent = initials;
    console.log("  ✓ Set initials:", initials);
  } else {
    console.warn(" Element #userInitials not found");
  }

  // 2. Set user name (use full_name if available, otherwise username)
  if (userName) {
    // If user has a full name, use it; otherwise use username
    const displayName = user.full_name || user.username;
    userName.textContent = displayName;
    console.log("  ✓ Set name:", displayName);
  } else {
    console.warn("Element #userName not found");
  }

  // 3. Set user email
  if (userEmail) {
    userEmail.textContent = user.email;
    console.log("  ✓ Set email:", user.email);
  } else {
    console.warn("Element #userEmail not found");
  }

  // 4. Set welcome name (use first name if full_name available)
  if (welcomeName) {
    let firstName = user.username; // Default to username

    // If user has full_name, extract first name
    if (user.full_name) {
      firstName = user.full_name.split(" ")[0]; // Get first word
    }

    welcomeName.textContent = firstName;
    console.log("  ✓ Set welcome name:", firstName);
  } else {
    console.warn("Element #welcomeName not found");
  }

  console.log("Header populated successfully");
}
// ========================================
// STEP 4: POPULATE STATS CARDS
// ========================================

/**
 * Populate stat cards with key user metrics
 *
 * Updates 4 stat cards:
 * 1. User ID - Database ID number
 * 2. Account Type - admin/standard_user (formatted)
 * 3. Preferred Units - metric/imperial (capitalized)
 * 4. Account Status - active/inactive (with emoji and color)
 *
 * @param {Object} user - User data from backend
 *
 * How it works:
 * 1. Get each stat element by ID
 * 2. Transform data for display (capitalize, format)
 * 3. Update text content
 * 4. Add colors/styling where needed
 */
function populateStats(user) {
  console.log("Populating stat cards...");

  // Card 1: User ID
  const statUserId = document.getElementById("statUserId");
  if (statUserId) {
    statUserId.textContent = user.user_id;
    console.log("  ✓ Set User ID:", user.user_id);
  } else {
    console.warn(" Element #statUserId not found");
  }

  // Card 2: Account Type
  // Convert "standard_user" → "Standard User"
  const statUserType = document.getElementById("statUserType");
  if (statUserType) {
    // Split by underscore: "standard_user" → ["standard", "user"]
    // Capitalize each word: ["Standard", "User"]
    // Join back: "Standard User"
    const userType = user.user_type
      .split("_") // Split by underscore
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1)) // Capitalize
      .join(" "); // Join with space

    statUserType.textContent = userType;
    console.log("  ✓ Set Account Type:", userType);
  } else {
    console.warn("Element #statUserType not found");
  }

  // Card 3: Preferred Units
  // Convert "metric" → "Metric"
  const statUnits = document.getElementById("statUnits");
  if (statUnits) {
    // Capitalize first letter
    const units =
      user.preferred_units.charAt(0).toUpperCase() +
      user.preferred_units.slice(1);

    statUnits.textContent = units;
    console.log("  ✓ Set Preferred Units:", units);
  } else {
    console.warn("Element #statUnits not found");
  }

  // Card 4: Account Status
  // Show "Active ✅" or "Inactive ❌" with color
  const statStatus = document.getElementById("statStatus");
  if (statStatus) {
    if (user.is_active) {
      // Active account
      statStatus.textContent = "Active ✅";
      statStatus.style.color = "#10b981"; // Green color
      console.log("  ✓ Set Account Status: Active");
    } else {
      // Inactive account
      statStatus.textContent = "Inactive ❌";
      statStatus.style.color = "#ef4444"; // Red color
      console.log("  ✓ Set Account Status: Inactive");
    }
  } else {
    console.warn("Element #statStatus not found");
  }

  console.log("Stats cards populated successfully");
}

// ========================================
// STEP 5: POPULATE DATA TABLE
// ========================================
/**
 * Populate detailed data table
 *
 * Shows all user information in a table format:
 * - User ID
 * - Username
 * - Email
 * - Full Name
 * - User Type
 * - Preferred Units
 * - Account Created (formatted date)
 * - Last Updated (formatted date)
 *
 * @param {Object} user - User data from backend
 *
 * How it works:
 * 1. Get each table cell element by ID
 * 2. Format data as needed
 * 3. Update text content
 * 4. Handle null values (show "Not provided")
 */
function populateDataTable(user) {
  console.log("Populating data table...");

  // User ID
  const dataUserId = document.getElementById("dataUserId");
  if (dataUserId) {
    dataUserId.textContent = user.user_id;
    console.log("  ✓ Set User ID:", user.user_id);
  }

  // Username
  const dataUsername = document.getElementById("dataUsername");
  if (dataUsername) {
    dataUsername.textContent = user.username;
    console.log("  ✓ Set Username:", user.username);
  }

  // Email
  const dataEmail = document.getElementById("dataEmail");
  if (dataEmail) {
    dataEmail.textContent = user.email;
    console.log("  ✓ Set Email:", user.email);
  }

  // Full Name (or "Not provided" if null)
  const dataFullName = document.getElementById("dataFullName");
  if (dataFullName) {
    dataFullName.textContent = user.full_name || "Not provided";
    console.log("  ✓ Set Full Name:", user.full_name || "Not provided");
  }

  // User Type (formatted)
  const dataUserType = document.getElementById("dataUserType");
  if (dataUserType) {
    const userType = user.user_type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
    dataUserType.textContent = userType;
    console.log("  ✓ Set User Type:", userType);
  }

  // Preferred Units (capitalized)
  const dataUnits = document.getElementById("dataUnits");
  if (dataUnits) {
    const units =
      user.preferred_units.charAt(0).toUpperCase() +
      user.preferred_units.slice(1);
    dataUnits.textContent = units;
    console.log("  ✓ Set Preferred Units:", units);
  }

  // Account Created (format date)
  const dataCreated = document.getElementById("dataCreated");
  if (dataCreated) {
    const createdDate = new Date(user.created_at);
    const formattedCreated = formatDateTime(createdDate);
    dataCreated.textContent = formattedCreated;
    console.log("  ✓ Set Account Created:", formattedCreated);
  }

  // Last Updated (format date)
  const dataUpdated = document.getElementById("dataUpdated");
  if (dataUpdated) {
    const updatedDate = new Date(user.updated_at);
    const formattedUpdated = formatDateTime(updatedDate);
    dataUpdated.textContent = formattedUpdated;
    console.log("  ✓ Set Last Updated:", formattedUpdated);
  }

  console.log("Data table populated successfully");
}

// ...existing code...

// ========================================
// STEP 6: DISPLAY TOKENS (DEBUG MODE)
// ========================================

/**
 * Display tokens for debugging
 *
 * Shows:
 * - Access Token (JWT)
 * - Refresh Token (if available)
 *
 * SECURITY NOTE: Remove this in production!
 * Tokens should never be displayed to users in real apps.
 * This is only for learning/debugging purposes.
 *
 * How it works:
 * 1. Get tokens from localStorage
 * 2. Display in <code> elements
 * 3. Show "Not available" if token doesn't exist
 */
function displayTokens() {
  console.log("🔑 Displaying tokens (DEBUG MODE)...");

  // Get tokens from localStorage
  const accessToken = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");

  // Display Access Token
  const accessTokenEl = document.getElementById("accessToken");
  if (accessTokenEl) {
    if (accessToken) {
      accessTokenEl.textContent = accessToken;
      console.log("  ✓ Access token displayed");
      console.log("    Length:", accessToken.length, "characters");
    } else {
      accessTokenEl.textContent = "Not available";
      console.log("No access token found");
    }
  } else {
    console.warn("Element #accessToken not found");
  }

  // Display Refresh Token
  const refreshTokenEl = document.getElementById("refreshToken");
  if (refreshTokenEl) {
    if (refreshToken) {
      refreshTokenEl.textContent = refreshToken;
      console.log("  ✓ Refresh token displayed");
      console.log("    Length:", refreshToken.length, "characters");
    } else {
      refreshTokenEl.textContent = "Not available";
      console.log("No refresh token found");
    }
  } else {
    console.warn("Element #refreshToken not found");
  }

  console.log("Tokens displayed");
}
// ========================================
// STEP 7: LOGOUT FUNCTIONALITY
// ========================================
function setupLogout() {
  console.log("🚪 Setting up logout button...");

  // Find logout button
  const logoutButton = document.getElementById("logoutButton");

  if (!logoutButton) {
    console.warn("Logout button not found");
    return;
  }

  // Add click event listener
  logoutButton.addEventListener("click", function () {
    console.log("User clicked logout");

    // Show confirmation dialog
    const confirmed = confirm("Are you sure you want to logout?");

    if (confirmed) {
      console.log("Logout confirmed");

      // Clear all authentication data from localStorage
      console.log("Clearing stored data...");
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      localStorage.removeItem("remember_me");

      console.log("All stored data cleared");

      // Redirect to login page
      console.log("Redirecting to login...");
      window.location.href = "/login.html";
    } else {
      console.log("Logout cancelled");
    }
  });

  console.log("Logout button setup complete");
}
// ========================================
// ACTIVE LOCATION MANAGEMENT
// ========================================

let activeLocationId = null; // Currently selected location

/**
 * Populate location selector dropdown
 * Uses userLocations from settings.js
 */
function populateLocationSelector() {
  console.log("📍 Populating location selector...");

  const select = document.getElementById("activeLocationSelect");

  if (!select) {
    console.warn("⚠️ Location selector not found");
    return;
  }

  // Clear existing options
  select.innerHTML = "";

  // Check if userLocations is available (loaded from settings.js)
  if (
    typeof userLocations === "undefined" ||
    !userLocations ||
    userLocations.length === 0
  ) {
    select.innerHTML = '<option value="">No locations added yet</option>';
    console.log("ℹ️ No user locations available");
    return;
  }

  // Add options for each user location
  userLocations.forEach((userLoc) => {
    // Find full location details
    const location = availableLocations.find(
      (loc) => loc.location_id === userLoc.location_id
    );

    if (!location) return;

    const option = document.createElement("option");
    option.value = userLoc.user_location_id;
    option.textContent = `${userLoc.custom_name} (${location.name})`;

    // Mark primary location as selected by default
    if (userLoc.is_primary) {
      option.selected = true;
      activeLocationId = userLoc.user_location_id;
    }

    select.appendChild(option);
  });

  console.log(`✅ Added ${userLocations.length} locations to selector`);
  console.log(`📍 Active location: ${activeLocationId}`);
}

/**
 * Handle location selection change
 */
function handleLocationChange() {
  console.log("🔄 Location changed");

  const select = document.getElementById("activeLocationSelect");
  const selectedId = parseInt(select.value);

  if (!selectedId) {
    console.warn("⚠️ No location selected");
    return;
  }

  activeLocationId = selectedId;

  // Find the selected location details
  const userLoc = userLocations.find(
    (ul) => ul.user_location_id === selectedId
  );

  if (userLoc) {
    const location = availableLocations.find(
      (loc) => loc.location_id === userLoc.location_id
    );
    console.log(
      `📍 Active location changed to: ${userLoc.custom_name} (${
        location ? location.name : "Unknown"
      })`
    );
  }

  // Reload all charts with new location's data
  refreshAllCharts();
}

/**
 * Load daily weather data and update chart
 */

/**
 * WEATHER FEATURES
 */

async function loadCurrentWeatherData() {
    console.log("🌡️ Loading current weather data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching current weather for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchCurrentData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Current weather data received:", response.data);
            updateCurrentWeatherCards(response.data);
        } else {
            console.warn("⚠️ No current weather data available");
            showCurrentWeatherError("No data available");
        }
    } catch (error) {
        console.error("❌ Error loading current weather data:", error);
        showCurrentWeatherError(error.message);
    }
}

/**
 * Update current weather cards with data
 */
function updateCurrentWeatherCards(data) {
    console.log("🎨 Updating current weather cards...");

    const container = document.getElementById("currentWeatherCards");
    if (!container) {
        console.warn("⚠️ Current weather cards container not found");
        return;
    }

    // Clear loading state
    container.innerHTML = "";

    // Weather code descriptions (WMO codes)
    const weatherDescriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thundersto rm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    };

    // Card 1: Temperature
    const tempCard = createWeatherCard({
        icon: "🌡️",
        title: "Temperature",
        value: data.temperature_2m,
        unit: "°C",
        subtitle: `Feels like ${data.apparent_temperature}°C`
    });

    // Card 2: Humidity
    const humidityCard = createWeatherCard({
        icon: "💧",
        title: "Humidity",
        value: data.relative_humidity_2m,
        unit: "%",
        subtitle: "Relative humidity"
    });

    // Card 3: Wind Speed
    const windCard = createWeatherCard({
        icon: "💨",
        title: "Wind Speed",
        value: data.wind_speed_10m,
        unit: "km/h",
        subtitle: `Direction: ${data.wind_direction_10m}°`
    });

    // Card 4: Precipitation
    const precipCard = createWeatherCard({
        icon: "🌧️",
        title: "Precipitation",
        value: data.precipitation,
        unit: "mm",
        subtitle: data.precipitation > 0 ? "Currently raining" : "No precipitation"
    });

    // Card 5: Cloud Cover
    const cloudCard = createWeatherCard({
        icon: "☁️",
        title: "Cloud Cover",
        value: data.cloud_cover,
        unit: "%",
        subtitle: data.cloud_cover > 75 ? "Very cloudy" : data.cloud_cover > 50 ? "Partly cloudy" : "Mostly clear"
    });

    // Card 6: Weather Code
    const weatherDesc = weatherDescriptions[data.weather_code] || "Unknown";
    const weatherCodeCard = createWeatherCard({
        icon: "🌤️",
        title: "Conditions",
        value: weatherDesc,
        unit: "",
        subtitle: `Code: ${data.weather_code}`,
        extraClass: "weather-code-card"
    });

    // Card 7: Model Info
    const modelCard = createWeatherCard({
        icon: "📡",
        title: "Data Source",
        value: data.model_name || "Open-Meteo",
        unit: "",
        subtitle: data.model_code || "OM_FORECAST",
        extraClass: "model-card"
    });

    // Append all cards
    container.appendChild(tempCard);
    container.appendChild(humidityCard);
    container.appendChild(windCard);
    container.appendChild(precipCard);
    container.appendChild(cloudCard);
    container.appendChild(weatherCodeCard);
    container.appendChild(modelCard);

    console.log("✅ Current weather cards updated");
}

function createWeatherCard({ icon, title, value, unit, subtitle, extraClass = "" }) {
    const card = document.createElement("div");
    card.className = `weather-card ${extraClass}`;

    card.innerHTML = `
        <div class="weather-card-header">
            <span class="weather-card-icon">${icon}</span>
            <span class="weather-card-title">${title}</span>
        </div>
        <div class="weather-card-value">
            ${typeof value === 'number' ? value.toFixed(1) : value}
            ${unit ? `<span class="weather-card-unit">${unit}</span>` : ''}
        </div>
        ${subtitle ? `<div class="weather-card-subtitle">${subtitle}</div>` : ''}
    `;

    return card;
}

async function loadDailyWeatherData() {
  console.log("🌤️ Loading daily weather data for location:", activeLocationId);

  if (!activeLocationId) {
    console.warn("⚠️ No active location selected");
    return;
  }

  try {
    // Get the actual location_id from user_locations
    const userLoc = userLocations.find(
      (ul) => ul.user_location_id === activeLocationId
    );
    if (!userLoc) {
      console.warn("⚠️ User location not found");
      return;
    }

    console.log(
      "📡 Fetching daily forecast for location_id:",
      userLoc.location_id
    );
    const response = await weatherApiClient.fetchDailyForecast(
      userLoc.location_id
    );

    if (response && response.data) {
      console.log("Daily weather data received:", response.data);
      updateWeatherDailyChart(response.data);
      updateWeatherPrecipChart(response.data);
      updateWeatherUvChart(response.data);
      updateWeatherWindChart(response.data);
    } else {
      console.warn("⚠️ No daily weather data available");
    }
  } catch (error) {
    console.error("❌ Error loading daily weather data:", error);
    // Optionally show user-friendly error message
  }
}

async function loadHourlyWeatherData() {
    console.log("⏰ Loading hourly weather data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching hourly weather for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchHourlyData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Hourly weather data received:", response.data);
            
            // Update all hourly weather charts
            updateWeatherHourlyTempChart(response.data);
            updateWeatherHourlyPrecipChart(response.data);
            updateWeatherHourlyWindChart(response.data);
        } else {
            console.warn("⚠️ No hourly weather data available");
        }
    } catch (error) {
        console.error("❌ Error loading hourly weather data:", error);
    }
}

/**
 * AIR QUALITY FEATURES
 */

async function loadCurrentAirQualityData() {
    console.log("🌫️ Loading current air quality data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching current air quality for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchAirQualityCurrentData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Current air quality data received:", response.data);
            updateCurrentAirQualityCards(response.data);
        } else {
            console.warn("⚠️ No current air quality data available");
            showCurrentAirQualityError("No data available");
        }
    } catch (error) {
        console.error("❌ Error loading current air quality data:", error);
        showCurrentAirQualityError(error.message);
    }
}

/**
 * Update current air quality cards with data
 */
function updateCurrentAirQualityCards(data) {
    console.log("🎨 Updating current air quality cards...");

    const container = document.getElementById("currentAirQualityCards");
    if (!container) {
        console.warn("⚠️ Current air quality cards container not found");
        return;
    }

    // Clear loading state
    container.innerHTML = "";

    /**
     * Get AQI level description and color
     * @param {number} aqi - AQI value
     * @param {string} standard - 'european' or 'us'
     * @returns {Object} - { level, color, emoji }
     */
    function getAQIInfo(aqi, standard = 'us') {
        if (standard === 'european') {
            // European AQI scale (0-100+)
            if (aqi <= 20) return { level: "Good", color: "#10b981", emoji: "🟢" };
            if (aqi <= 40) return { level: "Fair", color: "#84cc16", emoji: "🟡" };
            if (aqi <= 60) return { level: "Moderate", color: "#f59e0b", emoji: "🟠" };
            if (aqi <= 80) return { level: "Poor", color: "#ef4444", emoji: "🔴" };
            if (aqi <= 100) return { level: "Very Poor", color: "#991b1b", emoji: "🟣" };
            return { level: "Extremely Poor", color: "#7c2d12", emoji: "⚫" };
        } else {
            // US AQI scale (0-500)
            if (aqi <= 50) return { level: "Good", color: "#10b981", emoji: "🟢" };
            if (aqi <= 100) return { level: "Moderate", color: "#fbbf24", emoji: "🟡" };
            if (aqi <= 150) return { level: "Unhealthy for Sensitive Groups", color: "#f97316", emoji: "🟠" };
            if (aqi <= 200) return { level: "Unhealthy", color: "#ef4444", emoji: "🔴" };
            if (aqi <= 300) return { level: "Very Unhealthy", color: "#9333ea", emoji: "🟣" };
            return { level: "Hazardous", color: "#7c2d12", emoji: "⚫" };
        }
    }

    /**
     * Get pollutant level description
     * @param {number} value - Pollutant concentration
     * @param {string} pollutant - Pollutant type
     * @returns {string} - Level description
     */
    function getPollutantLevel(value, pollutant) {
        if (value === null || value === undefined) return "N/A";
        
        switch(pollutant) {
            case 'pm2_5':
                if (value <= 12) return "Good";
                if (value <= 35.4) return "Moderate";
                if (value <= 55.4) return "Unhealthy for Sensitive";
                if (value <= 150.4) return "Unhealthy";
                if (value <= 250.4) return "Very Unhealthy";
                return "Hazardous";
            case 'pm10':
                if (value <= 54) return "Good";
                if (value <= 154) return "Moderate";
                if (value <= 254) return "Unhealthy for Sensitive";
                if (value <= 354) return "Unhealthy";
                if (value <= 424) return "Very Unhealthy";
                return "Hazardous";
            case 'no2':
                if (value <= 53) return "Good";
                if (value <= 100) return "Moderate";
                return "Unhealthy";
            case 'o3':
                if (value <= 54) return "Good";
                if (value <= 70) return "Moderate";
                return "Unhealthy";
            case 'so2':
                if (value <= 35) return "Good";
                if (value <= 75) return "Moderate";
                return "Unhealthy";
            case 'co':
                if (value <= 4400) return "Good";
                if (value <= 9400) return "Moderate";
                return "Unhealthy";
            default:
                return "Unknown";
        }
    }

    // Get AQI info for styling
    const europeanAQIInfo = getAQIInfo(data.european_aqi, 'european');
    const usAQIInfo = getAQIInfo(data.us_aqi, 'us');

    // Card 1: European AQI
    const europeanAQICard = createAirQualityCard({
        icon: europeanAQIInfo.emoji,
        title: "European AQI",
        value: data.european_aqi,
        unit: "",
        subtitle: europeanAQIInfo.level,
        extraClass: "aqi-card",
        backgroundColor: europeanAQIInfo.color
    });

    // Card 2: US AQI
    const usAQICard = createAirQualityCard({
        icon: usAQIInfo.emoji,
        title: "US AQI",
        value: data.us_aqi,
        unit: "",
        subtitle: usAQIInfo.level,
        extraClass: "aqi-card",
        backgroundColor: usAQIInfo.color
    });

    // Card 3: PM2.5
    const pm25Card = createAirQualityCard({
        icon: "🔴",
        title: "PM2.5",
        value: data.pm2_5,
        unit: "µg/m³",
        subtitle: getPollutantLevel(data.pm2_5, 'pm2_5')
    });

    // Card 4: PM10
    const pm10Card = createAirQualityCard({
        icon: "🟤",
        title: "PM10",
        value: data.pm10,
        unit: "µg/m³",
        subtitle: getPollutantLevel(data.pm10, 'pm10')
    });

    // Card 5: Nitrogen Dioxide (NO2)
    const no2Card = createAirQualityCard({
        icon: "🟡",
        title: "Nitrogen Dioxide",
        value: data.nitrogen_dioxide,
        unit: "µg/m³",
        subtitle: getPollutantLevel(data.nitrogen_dioxide, 'no2')
    });

    // Card 6: Ozone (O3)
    const o3Card = createAirQualityCard({
        icon: "🔵",
        title: "Ozone",
        value: data.ozone,
        unit: "µg/m³",
        subtitle: getPollutantLevel(data.ozone, 'o3')
    });

    // Card 7: Sulphur Dioxide (SO2)
    const so2Card = createAirQualityCard({
        icon: "🟢",
        title: "Sulphur Dioxide",
        value: data.sulphur_dioxide,
        unit: "µg/m³",
        subtitle: getPollutantLevel(data.sulphur_dioxide, 'so2')
    });

    // Card 8: Carbon Monoxide (CO)
    const coCard = createAirQualityCard({
        icon: "⚫",
        title: "Carbon Monoxide",
        value: data.carbon_monoxide,
        unit: "µg/m³",
        subtitle: getPollutantLevel(data.carbon_monoxide, 'co')
    });

    // Card 9: Dust
    const dustCard = createAirQualityCard({
        icon: "🟫",
        title: "Dust",
        value: data.dust,
        unit: "µg/m³",
        subtitle: data.dust > 50 ? "High" : data.dust > 20 ? "Moderate" : "Low"
    });

    // Card 10: Ammonia (if available)
    if (data.ammonia !== null && data.ammonia !== undefined) {
        const ammoniaCard = createAirQualityCard({
            icon: "💨",
            title: "Ammonia",
            value: data.ammonia,
            unit: "µg/m³",
            subtitle: data.ammonia > 100 ? "High" : "Normal"
        });
        container.appendChild(ammoniaCard);
    }

    // Append all cards
    container.appendChild(europeanAQICard);
    container.appendChild(usAQICard);
    container.appendChild(pm25Card);
    container.appendChild(pm10Card);
    container.appendChild(no2Card);
    container.appendChild(o3Card);
    container.appendChild(so2Card);
    container.appendChild(coCard);
    container.appendChild(dustCard);

    console.log("✅ Current air quality cards updated");
}

/**
 * Create an air quality card element
 */
function createAirQualityCard({ icon, title, value, unit, subtitle, extraClass = "", backgroundColor = null }) {
    const card = document.createElement("div");
    card.className = `weather-card ${extraClass}`;
    
    // Apply custom background color if provided (for AQI cards)
    if (backgroundColor) {
        card.style.background = `linear-gradient(135deg, ${backgroundColor} 0%, ${backgroundColor}dd 100%)`;
        card.style.color = "white";
        // Make all text white for colored cards
        card.classList.add("colored-card");
    }

    // Handle null/undefined values
    const displayValue = (value === null || value === undefined) 
        ? "N/A" 
        : (typeof value === 'number' ? value.toFixed(1) : value);

    card.innerHTML = `
        <div class="weather-card-header">
            <span class="weather-card-icon">${icon}</span>
            <span class="weather-card-title">${title}</span>
        </div>
        <div class="weather-card-value">
            ${displayValue}
            ${unit && value !== null && value !== undefined ? `<span class="weather-card-unit">${unit}</span>` : ''}
        </div>
        ${subtitle ? `<div class="weather-card-subtitle">${subtitle}</div>` : ''}
    `;

    return card;
}

async function loadHourlyAirQualityData() {
    console.log("🌫️ Loading hourly air quality data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching hourly air quality for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchAirQualityHourlyData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Hourly air quality data received:", response.data);
            
            // Update all air quality charts
            updateAirQualityAqiChart(response.data);
            updateAirQualityPollutantsChart(response.data);
            updateAirQualitySecondaryChart(response.data);
        } else {
            console.warn("⚠️ No hourly air quality data available");
        }
    } catch (error) {
        console.error("❌ Error loading hourly air quality data:", error);
    }
}

/**
 * MARINE FEATURES
 */
async function loadCurrentMarineData() {
    console.log("🌊 Loading current marine data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching current marine data for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchMarineCurrentData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Current marine data received:", response.data);
            updateCurrentMarineCards(response.data);
        } else {
            console.warn("⚠️ No current marine data available");
            showCurrentMarineError("No data available");
        }
    } catch (error) {
        console.error("❌ Error loading current marine data:", error);
        showCurrentMarineError(error.message);
    }
}

/**
 * Update current marine cards with data
 */
function updateCurrentMarineCards(data) {
    console.log("🎨 Updating current marine cards...");

    const container = document.getElementById("currentMarineCards");
    if (!container) {
        console.warn("⚠️ Current marine cards container not found");
        return;
    }

    // Clear loading state
    container.innerHTML = "";

    /**
     * Get wave height description
     * @param {number} height - Wave height in meters
     * @returns {string} Description
     */
    function getWaveDescription(height) {
        if (height < 0.5) return "Calm seas";
        if (height < 1.25) return "Light waves";
        if (height < 2.5) return "Moderate waves";
        if (height < 4) return "Rough seas";
        if (height < 6) return "Very rough";
        if (height < 9) return "High seas";
        return "Very high seas";
    }

    /**
     * Get wave period description
     * @param {number} period - Wave period in seconds
     * @returns {string} Description
     */
    function getWavePeriodDescription(period) {
        if (period < 5) return "Short period";
        if (period < 8) return "Medium period";
        if (period < 12) return "Long period";
        return "Very long period";
    }

    /**
     * Get ocean current speed description
     * @param {number} velocity - Current velocity in m/s
     * @returns {string} Description
     */
    function getCurrentDescription(velocity) {
        if (velocity < 0.25) return "Weak current";
        if (velocity < 0.5) return "Moderate current";
        if (velocity < 1.0) return "Strong current";
        if (velocity < 2.0) return "Very strong current";
        return "Extreme current";
    }

    /**
     * Get temperature description
     * @param {number} temp - Temperature in °C
     * @returns {string} Description
     */
    function getTempDescription(temp) {
        if (temp < 10) return "Very cold";
        if (temp < 15) return "Cold";
        if (temp < 20) return "Cool";
        if (temp < 25) return "Comfortable";
        if (temp < 30) return "Warm";
        return "Very warm";
    }

    /**
     * Convert degrees to compass direction
     * @param {number} degrees - Direction in degrees
     * @returns {string} Compass direction
     */
    function getCompassDirection(degrees) {
        const directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                          "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
        const index = Math.round(degrees / 22.5) % 16;
        return directions[index];
    }

    // Card 1: Wave Height
    const waveHeightCard = createMarineCard({
        icon: "🌊",
        title: "Wave Height",
        value: data.wave_height,
        unit: "m",
        subtitle: getWaveDescription(data.wave_height)
    });

    // Card 2: Wave Direction
    const waveDirectionCard = createMarineCard({
        icon: "🧭",
        title: "Wave Direction",
        value: `${getCompassDirection(data.wave_direction)}`,
        unit: "",
        subtitle: `${data.wave_direction}°`
    });

    // Card 3: Wave Period
    const wavePeriodCard = createMarineCard({
        icon: "⏱️",
        title: "Wave Period",
        value: data.wave_period,
        unit: "s",
        subtitle: getWavePeriodDescription(data.wave_period)
    });

    // Card 4: Swell Wave Height
    const swellHeightCard = createMarineCard({
        icon: "🌀",
        title: "Swell Height",
        value: data.swell_wave_height,
        unit: "m",
        subtitle: `Direction: ${getCompassDirection(data.swell_wave_direction)} (${data.swell_wave_direction}°)`
    });

    // Card 5: Swell Wave Period
    const swellPeriodCard = createMarineCard({
        icon: "🔄",
        title: "Swell Period",
        value: data.swell_wave_period,
        unit: "s",
        subtitle: getWavePeriodDescription(data.swell_wave_period)
    });

    // Card 6: Wind Wave Height
    const windWaveCard = createMarineCard({
        icon: "💨",
        title: "Wind Wave Height",
        value: data.wind_wave_height,
        unit: "m",
        subtitle: data.wind_wave_height < 0.5 ? "Low wind waves" : "Moderate wind waves"
    });

    // Card 7: Sea Surface Temperature
    const tempCard = createMarineCard({
        icon: "🌡️",
        title: "Sea Temperature",
        value: data.sea_surface_temperature,
        unit: "°C",
        subtitle: getTempDescription(data.sea_surface_temperature)
    });

    // Card 8: Ocean Current Velocity
    const currentVelocityCard = createMarineCard({
        icon: "➡️",
        title: "Current Speed",
        value: data.ocean_current_velocity,
        unit: "m/s",
        subtitle: getCurrentDescription(data.ocean_current_velocity)
    });

    // Card 9: Ocean Current Direction
    const currentDirectionCard = createMarineCard({
        icon: "🧭",
        title: "Current Direction",
        value: `${getCompassDirection(data.ocean_current_direction)}`,
        unit: "",
        subtitle: `${data.ocean_current_direction}°`
    });

    // Append all cards
    container.appendChild(waveHeightCard);
    container.appendChild(waveDirectionCard);
    container.appendChild(wavePeriodCard);
    container.appendChild(swellHeightCard);
    container.appendChild(swellPeriodCard);
    container.appendChild(windWaveCard);
    container.appendChild(tempCard);
    container.appendChild(currentVelocityCard);
    container.appendChild(currentDirectionCard);

    console.log("✅ Current marine cards updated");
}

/**
 * Create a marine card element
 */
function createMarineCard({ icon, title, value, unit, subtitle, extraClass = "" }) {
    const card = document.createElement("div");
    card.className = `weather-card ${extraClass}`;

    // Handle null/undefined values
    const displayValue = (value === null || value === undefined) 
        ? "N/A" 
        : (typeof value === 'number' ? value.toFixed(2) : value);

    card.innerHTML = `
        <div class="weather-card-header">
            <span class="weather-card-icon">${icon}</span>
            <span class="weather-card-title">${title}</span>
        </div>
        <div class="weather-card-value">
            ${displayValue}
            ${unit && value !== null && value !== undefined ? `<span class="weather-card-unit">${unit}</span>` : ''}
        </div>
        ${subtitle ? `<div class="weather-card-subtitle">${subtitle}</div>` : ''}
    `;

    return card;
}

/**
 * Show error message in current marine section
 */
function showCurrentMarineError(message) {
    const container = document.getElementById("currentMarineCards");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-spinner" style="color: #ef4444;">
            ❌ ${message}
        </div>
    `;
}async function loadCurrentMarineData() {
    console.log("🌊 Loading current marine data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching current marine data for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchMarineCurrentData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Current marine data received:", response.data);
            updateCurrentMarineCards(response.data);
        } else {
            console.warn("⚠️ No current marine data available");
            showCurrentMarineError("No data available");
        }
    } catch (error) {
        console.error("❌ Error loading current marine data:", error);
        showCurrentMarineError(error.message);
    }
}

/**
 * Update current marine cards with data
 */
function updateCurrentMarineCards(data) {
    console.log("🎨 Updating current marine cards...");

    const container = document.getElementById("currentMarineCards");
    if (!container) {
        console.warn("⚠️ Current marine cards container not found");
        return;
    }

    // Clear loading state
    container.innerHTML = "";

    /**
     * Get wave height description
     * @param {number} height - Wave height in meters
     * @returns {string} Description
     */
    function getWaveDescription(height) {
        if (height < 0.5) return "Calm seas";
        if (height < 1.25) return "Light waves";
        if (height < 2.5) return "Moderate waves";
        if (height < 4) return "Rough seas";
        if (height < 6) return "Very rough";
        if (height < 9) return "High seas";
        return "Very high seas";
    }

    /**
     * Get wave period description
     * @param {number} period - Wave period in seconds
     * @returns {string} Description
     */
    function getWavePeriodDescription(period) {
        if (period < 5) return "Short period";
        if (period < 8) return "Medium period";
        if (period < 12) return "Long period";
        return "Very long period";
    }

    /**
     * Get ocean current speed description
     * @param {number} velocity - Current velocity in m/s
     * @returns {string} Description
     */
    function getCurrentDescription(velocity) {
        if (velocity < 0.25) return "Weak current";
        if (velocity < 0.5) return "Moderate current";
        if (velocity < 1.0) return "Strong current";
        if (velocity < 2.0) return "Very strong current";
        return "Extreme current";
    }

    /**
     * Get temperature description
     * @param {number} temp - Temperature in °C
     * @returns {string} Description
     */
    function getTempDescription(temp) {
        if (temp < 10) return "Very cold";
        if (temp < 15) return "Cold";
        if (temp < 20) return "Cool";
        if (temp < 25) return "Comfortable";
        if (temp < 30) return "Warm";
        return "Very warm";
    }

    /**
     * Convert degrees to compass direction
     * @param {number} degrees - Direction in degrees
     * @returns {string} Compass direction
     */
    function getCompassDirection(degrees) {
        const directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                          "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
        const index = Math.round(degrees / 22.5) % 16;
        return directions[index];
    }

    // Card 1: Wave Height
    const waveHeightCard = createMarineCard({
        icon: "🌊",
        title: "Wave Height",
        value: data.wave_height,
        unit: "m",
        subtitle: getWaveDescription(data.wave_height)
    });

    // Card 2: Wave Direction
    const waveDirectionCard = createMarineCard({
        icon: "🧭",
        title: "Wave Direction",
        value: `${getCompassDirection(data.wave_direction)}`,
        unit: "",
        subtitle: `${data.wave_direction}°`
    });

    // Card 3: Wave Period
    const wavePeriodCard = createMarineCard({
        icon: "⏱️",
        title: "Wave Period",
        value: data.wave_period,
        unit: "s",
        subtitle: getWavePeriodDescription(data.wave_period)
    });

    // Card 4: Swell Wave Height
    const swellHeightCard = createMarineCard({
        icon: "🌀",
        title: "Swell Height",
        value: data.swell_wave_height,
        unit: "m",
        subtitle: `Direction: ${getCompassDirection(data.swell_wave_direction)} (${data.swell_wave_direction}°)`
    });

    // Card 5: Swell Wave Period
    const swellPeriodCard = createMarineCard({
        icon: "🔄",
        title: "Swell Period",
        value: data.swell_wave_period,
        unit: "s",
        subtitle: getWavePeriodDescription(data.swell_wave_period)
    });

    // Card 6: Wind Wave Height
    const windWaveCard = createMarineCard({
        icon: "💨",
        title: "Wind Wave Height",
        value: data.wind_wave_height,
        unit: "m",
        subtitle: data.wind_wave_height < 0.5 ? "Low wind waves" : "Moderate wind waves"
    });

    // Card 7: Sea Surface Temperature
    const tempCard = createMarineCard({
        icon: "🌡️",
        title: "Sea Temperature",
        value: data.sea_surface_temperature,
        unit: "°C",
        subtitle: getTempDescription(data.sea_surface_temperature)
    });

    // Card 8: Ocean Current Velocity
    const currentVelocityCard = createMarineCard({
        icon: "➡️",
        title: "Current Speed",
        value: data.ocean_current_velocity,
        unit: "m/s",
        subtitle: getCurrentDescription(data.ocean_current_velocity)
    });

    // Card 9: Ocean Current Direction
    const currentDirectionCard = createMarineCard({
        icon: "🧭",
        title: "Current Direction",
        value: `${getCompassDirection(data.ocean_current_direction)}`,
        unit: "",
        subtitle: `${data.ocean_current_direction}°`
    });

    // Append all cards
    container.appendChild(waveHeightCard);
    container.appendChild(waveDirectionCard);
    container.appendChild(wavePeriodCard);
    container.appendChild(swellHeightCard);
    container.appendChild(swellPeriodCard);
    container.appendChild(windWaveCard);
    container.appendChild(tempCard);
    container.appendChild(currentVelocityCard);
    container.appendChild(currentDirectionCard);

    console.log("✅ Current marine cards updated");
}

/**
 * Create a marine card element
 */
function createMarineCard({ icon, title, value, unit, subtitle, extraClass = "" }) {
    const card = document.createElement("div");
    card.className = `weather-card ${extraClass}`;

    // Handle null/undefined values
    const displayValue = (value === null || value === undefined) 
        ? "N/A" 
        : (typeof value === 'number' ? value.toFixed(2) : value);

    card.innerHTML = `
        <div class="weather-card-header">
            <span class="weather-card-icon">${icon}</span>
            <span class="weather-card-title">${title}</span>
        </div>
        <div class="weather-card-value">
            ${displayValue}
            ${unit && value !== null && value !== undefined ? `<span class="weather-card-unit">${unit}</span>` : ''}
        </div>
        ${subtitle ? `<div class="weather-card-subtitle">${subtitle}</div>` : ''}
    `;

    return card;
}

async function loadDailyMarineData() {
    console.log("🌊 Loading daily marine data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching daily marine forecast for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchMarineDailyData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Daily marine data received:", response.data);
            
            // Update all daily marine charts
            updateMarineDailyWaveChart(response.data);
            updateMarineDailyPeriodChart(response.data);
        } else {
            console.warn("⚠️ No daily marine data available");
        }
    } catch (error) {
        console.error("❌ Error loading daily marine data:", error);
    }
}

async function loadHourlyMarineData() {
    console.log("🌊 Loading hourly marine data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching hourly marine forecast for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchMarineHourlyData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Hourly marine data received:", response.data);
            
            // Update all hourly marine charts
            updateMarineHourlyWaveChart(response.data);
            updateMarineHourlyPeriodChart(response.data);
        } else {
            console.warn("⚠️ No hourly marine data available");
        }
    } catch (error) {
        console.error("❌ Error loading hourly marine data:", error);
    }
}

async function loadDailySatelliteData() {
    console.log("🛰️ Loading daily satellite data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching daily satellite data for location_id:", userLoc.location_id);
        const response = await weatherApiClient.fetchSatelliteDailyData(userLoc.location_id);

        if (response && response.data) {
            console.log("✅ Daily satellite data received:", response.data);
            
            // Update all daily satellite charts
            updateSatelliteDailyRadiationChart(response.data);
            updateSatelliteDailyIrradianceChart(response.data);
        } else {
            console.warn("⚠️ No daily satellite data available");
        }
    } catch (error) {
        console.error("❌ Error loading daily satellite data:", error);
    }
}
async function loadClimateProjectionData() {
    console.log("🌍 Loading climate projection data for location:", activeLocationId);

    if (!activeLocationId) {
        console.warn("⚠️ No active location selected");
        return;
    }

    try {
        // Get the actual location_id from user_locations
        const userLoc = userLocations.find(
            (ul) => ul.user_location_id === activeLocationId
        );
        if (!userLoc) {
            console.warn("⚠️ User location not found");
            return;
        }

        console.log("📡 Fetching climate projection for location_id:", userLoc.location_id);
        
        // Default model: EC_Earth3P_HR
        // Date range: 2022-01-01 to 2026-12-31 (5 years)
        const response = await weatherApiClient.fetchClimateProjection(
            userLoc.location_id,
            'EC_Earth3P_HR',
            '2022-01-01',
            '2026-12-31'
        );

        if (response && response.data) {
            console.log("✅ Climate projection data received:", response.data);
            console.log(`   Model: ${response.data.model_name}`);
            console.log(`   Period: ${response.data.start_date} to ${response.data.end_date}`);
            console.log(`   Total days: ${response.data.total_days}`);
            
            // Update model info card
            updateClimateModelInfo(response.data);
            
            // Update all climate charts
            updateClimateTempTrendsChart(response.data);
            updateClimatePrecipHumidityChart(response.data);
            updateClimateWindRadiationChart(response.data);
        } else {
            console.warn("⚠️ No climate projection data available");
            showClimateError("No data available for this location");
        }
    } catch (error) {
        console.error("❌ Error loading climate projection data:", error);
        showClimateError(error.message);
    }
}

/**
 * Update climate model information card
 */
function updateClimateModelInfo(data) {
    console.log("🎨 Updating climate model info cards...");

    const container = document.getElementById("climateModelInfo");
    if (!container) {
        console.warn("⚠️ Climate model info container not found");
        return;
    }

    // Clear loading state
    container.innerHTML = "";

    // Card 1: Climate Model
    const modelCard = createClimateCard({
        icon: "🌍",
        title: "Climate Model",
        value: data.model_name,
        subtitle: data.model_code,
        extraClass: "model-card"
    });

    // Card 2: Projection Period
    const periodCard = createClimateCard({
        icon: "📅",
        title: "Projection Period",
        value: `${new Date(data.start_date).getFullYear()}-${new Date(data.end_date).getFullYear()}`,
        subtitle: `${data.total_days} days`
    });

    // Card 3: Data Points
    const dataPointsCard = createClimateCard({
        icon: "📊",
        title: "Data Points",
        value: data.daily_data.length.toLocaleString(),
        subtitle: "Daily observations"
    });

    // Card 4: Spatial Resolution
    const resolutionCard = createClimateCard({
        icon: "🎯",
        title: "Resolution",
        value: "25 km",
        subtitle: "Spatial resolution"
    });

    // Append all cards
    container.appendChild(modelCard);
    container.appendChild(periodCard);
    container.appendChild(dataPointsCard);
    container.appendChild(resolutionCard);

    console.log("✅ Climate model info cards updated");
}

/**
 * Create a climate info card element
 */
function createClimateCard({ icon, title, value, subtitle, extraClass = "" }) {
    const card = document.createElement("div");
    card.className = `climate-card ${extraClass}`;

    card.innerHTML = `
        <div class="climate-card-header">
            <span class="climate-card-icon">${icon}</span>
            <span class="climate-card-title">${title}</span>
        </div>
        <div class="climate-card-value">${value}</div>
        ${subtitle ? `<div class="climate-card-subtitle">${subtitle}</div>` : ''}
    `;

    return card;
}

/**
 * Show error message in climate section
 */
function showClimateError(message) {
    const container = document.getElementById("climateModelInfo");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-spinner" style="color: #ef4444;">
            ❌ ${message}
        </div>
    `;
}

/**
 * Show error message in current marine section
 */
function showCurrentMarineError(message) {
    const container = document.getElementById("currentMarineCards");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-spinner" style="color: #ef4444;">
            ❌ ${message}
        </div>
    `;
}


function showCurrentAirQualityError(message) {
    const container = document.getElementById("currentAirQualityCards");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-spinner" style="color: #ef4444;">
            ❌ ${message}
        </div>
    `;
}
function showCurrentWeatherError(message) {
    const container = document.getElementById("currentWeatherCards");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-spinner" style="color: #ef4444;">
            ❌ ${message}
        </div>
    `;
}

/**
 * Refresh all charts with current location's data
 */
function refreshAllCharts() {
  console.log("🔄 Refreshing all charts for location:", activeLocationId);

  // Show loading state on refresh button
  const refreshBtn = document.getElementById("refreshDataBtn");
  if (refreshBtn) {
    refreshBtn.classList.add("rotating");
  }

  loadCurrentWeatherData();
  loadDailyWeatherData();
  loadHourlyWeatherData();
  loadCurrentAirQualityData();
  loadHourlyAirQualityData();
  loadCurrentMarineData();
  loadDailyMarineData();
  loadHourlyMarineData();
  loadDailySatelliteData();
  loadClimateProjectionData()


  // Remove loading state after a short delay
  setTimeout(() => {
    if (refreshBtn) {
      refreshBtn.classList.remove("rotating");
    }
    console.log("✅ Charts refreshed");
  }, 1000);
}

function initializeSidebar() {
  console.log("🧭 Initializing sidebar navigation...");

  const sidebarItems = document.querySelectorAll(".sidebar-item");
  const contentSections = document.querySelectorAll(".content-section");

  sidebarItems.forEach((item) => {
    item.addEventListener("click", function () {
      const sectionId = this.getAttribute("data-section");

      // Remove active class from all sidebar items
      sidebarItems.forEach((i) => i.classList.remove("active"));

      // Add active class to clicked item
      this.classList.add("active");

      // Hide all content sections
      contentSections.forEach((section) => section.classList.remove("active"));

      // Show selected section
      const targetSection = document.getElementById(`section-${sectionId}`);
      if (targetSection) {
        targetSection.classList.add("active");
        console.log(`📄 Switched to section: ${sectionId}`);
      }
    });
  });

  console.log("✅ Sidebar navigation initialized");
}

// Call sidebar initialization when DOM is ready

/**
 * Setup logout button
 *
 * Adds click handler to logout button that:
 * 1. Shows confirmation dialog
 * 2. Clears all stored data (tokens, user data)
 * 3. Redirects to login page
 *
 * How it works:
 * 1. Find logout button by ID
 * 2. Add click event listener
 * 3. Confirm user wants to logout
 * 4. Clear localStorage
 * 5. Redirect to login
 */

// ========================================
// HELPER: FORMAT DATE AND TIME
// ========================================

/**
 * Format date and time for display
 *
 * Converts ISO date string to readable format:
 * "2025-11-06T17:11:22" → "November 6, 2025 at 5:11 PM"
 *
 * @param {Date} date - Date object to format
 * @returns {string} Formatted date string
 *
 * How it works:
 * 1. Takes a Date object
 * 2. Uses toLocaleString() with options
 * 3. Returns human-readable date/time
 */
function formatDateTime(date) {
  const options = {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  };

  return date.toLocaleString("en-US", options);
}

// ========================================
// INITIALIZE DASHBOARD
// ========================================

document.addEventListener("DOMContentLoaded", async function () {
  console.log("🚀 DOM loaded - Initializing dashboard...");

  // STEP 1: Check authentication first
  if (!checkAuthentication()) {
    return; // Stop if not authenticated
  }

  // STEP 2: Initialize sidebar navigation
  initializeSidebar();

  // STEP 3: Fetch and display user data
  try {
    console.log("\n--- Fetching User Data ---");
    const userData = await fetchUserData();

    if (userData) {
      console.log("\n--- User Data Successfully Retrieved ---");
      console.log("User ID:", userData.user_id);
      console.log("Username:", userData.username);
      console.log("Email:", userData.email);
      console.log("Full Name:", userData.full_name);
      console.log("User Type:", userData.user_type);
      console.log("Preferred Units:", userData.preferred_units);
      console.log("Account Active:", userData.is_active);
      console.log("Created:", userData.created_at);
      console.log("Updated:", userData.updated_at);

      console.log("\n--- Populating Dashboard ---");
      populateHeader(userData);
      populateStats(userData);
      populateDataTable(userData);
      displayTokens();
      setupLogout();
    }
  } catch (error) {
    console.error("❌ Failed to fetch user data:", error);
    alert("Failed to load dashboard. Please try logging in again.");
    window.location.href = "/login.html";
    return;
  }

  // STEP 4: Initialize settings and load user locations
  console.log("\n--- Initializing Settings ---");
  if (typeof initializeSettings === "function") {
    await initializeSettings(); // This loads availableLocations and userLocations
  } else {
    console.warn("⚠️ initializeSettings function not found!");
  }

  // STEP 5: Populate location selector after settings are ready
  console.log("\n--- Setting Up Location Selector ---");
  populateLocationSelector();

  // STEP 6: Set up event listeners
  const locationSelect = document.getElementById("activeLocationSelect");
  if (locationSelect) {
    locationSelect.addEventListener("change", handleLocationChange);
    console.log("✅ Location change listener added");
  }

  const refreshBtn = document.getElementById("refreshDataBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", refreshAllCharts);
    console.log("✅ Refresh button listener added");
  }

  initializeWeatherCharts();

  // STEP 7: Load initial charts for selected location
  console.log("\n--- Loading Charts ---");
  refreshAllCharts();
  window.setInterval(refreshAllCharts, 60 * 1000);

  console.log("\n✅ Dashboard fully initialized!");
});
