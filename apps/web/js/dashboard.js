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
      console.log("✅ Daily weather data received:", response.data);
      updateWeatherDailyChart(response.data);
    } else {
      console.warn("⚠️ No daily weather data available");
    }
  } catch (error) {
    console.error("❌ Error loading daily weather data:", error);
    // Optionally show user-friendly error message
  }
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

  // Load real daily weather data
  loadDailyWeatherData();

  // For now, recreate other charts with sample data
  if (typeof createWeatherWindChart === "function") {
    createWeatherWindChart([]);
  }

  if (typeof createAirQualityChart === "function") {
    createAirQualityChart([]);
  }

  if (typeof createMarineWaveChart === "function") {
    createMarineWaveChart([]);
  }

  if (typeof createSatelliteChart === "function") {
    createSatelliteChart([]);
  }
  if (typeof createClimateTempChart === "function") {
    createClimateTempChart([]);
  }

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
