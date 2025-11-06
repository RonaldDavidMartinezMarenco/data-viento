/**
 * DataViento - Dashboard Page Logic
 * 
 * Responsibilities:
 * 1. Check if user is authenticated
 * 2. Fetch user data from backend API
 * 3. Populate dashboard with user information
 * 4. Handle logout functionality
 */

console.log('dashboard.js loaded');

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
    console.log('🔒 Checking authentication...');
    
    // Try to get token from localStorage
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        // No token = not logged in
        console.log('❌ No access token found, redirecting to login');
        window.location.href = '/login.html';
        return false;
    }
    
    console.log('✅ Access token found:', token.substring(0, 20) + '...');
    return true;
}

// ========================================
// STEP 2: FETCH USER DATA FROM BACKEND
// ========================================

/**
 * Fetch current user data from backend
 * 
 * Makes authenticated request to GET /users/me endpoint
 * Backend will:
 * 1. Validate JWT token
 * 2. Extract user_id from token
 * 3. Query database for user data
 * 4. Return user profile (without password)
 * 
 * Returns:
 *   Promise<Object>: User data
 *   
 * Throws:
 *   Error if request fails or user not authenticated
 */
async function fetchUserData() {
    console.log('📡 Fetching user data from backend...');
    
    try {
        // Get token from localStorage
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            throw new Error('No access token available');
        }
        
        // Make authenticated request to backend
        // This calls: GET http://localhost:8000/users/me
        const apiUrl = getApiUrl('/users/me');
        console.log('🔗 API URL:', apiUrl);
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,  // ← JWT token in header
                'Content-Type': 'application/json'
            }
        });
        
        console.log('📥 Response status:', response.status);
        
        // Check if request was successful
        if (!response.ok) {
            // If 401 Unauthorized, token is invalid/expired
            if (response.status === 401) {
                console.log('❌ Token invalid or expired, redirecting to login');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.location.href = '/login.html';
                return null;
            }
            
            // Other error
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch user data');
        }
        
        // Parse response JSON
        const userData = await response.json();
        console.log('✅ User data received:', userData);
        
        // Store user data in localStorage for quick access
        localStorage.setItem('user', JSON.stringify(userData));
        
        return userData;
        
    } catch (error) {
        console.error('💥 Error fetching user data:', error);
        throw error;
    }
}

// ========================================
// STEP 3: POPULATE DASHBOARD WITH DATA
// ========================================

/**
 * Populate header section with user info
 * 
 * Updates:
 * - User avatar initials (first letter of username)
 * - User full name or username
 * - User email
 * 
 * @param {Object} user - User data from backend
 */
function populateHeader(user) {
    console.log('📝 Populating header with user info...');
    
    // Get DOM elements
    const userInitials = document.getElementById('userInitials');
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');
    const welcomeName = document.getElementById('welcomeName');
    
    // Set user initials (first letter of username, uppercase)
    if (userInitials) {
        const initials = user.username.charAt(0).toUpperCase();
        userInitials.textContent = initials;
        console.log('  ✓ Set initials:', initials);
    }
    
    // Set user name (use full_name if available, otherwise username)
    if (userName) {
        const displayName = user.full_name || user.username;
        userName.textContent = displayName;
        console.log('  ✓ Set name:', displayName);
    }
    
    // Set user email
    if (userEmail) {
        userEmail.textContent = user.email;
        console.log('  ✓ Set email:', user.email);
    }
    
    // Set welcome name (use first name if full_name available)
    if (welcomeName) {
        let firstName = user.username;
        if (user.full_name) {
            firstName = user.full_name.split(' ')[0]; // Get first name
        }
        welcomeName.textContent = firstName;
        console.log('  ✓ Set welcome name:', firstName);
    }
}

/**
 * Populate stat cards with key user metrics
 * 
 * Updates 4 stat cards:
 * 1. User ID
 * 2. Account Type (admin/standard_user)
 * 3. Preferred Units (metric/imperial)
 * 4. Account Status (active/inactive)
 * 
 * @param {Object} user - User data from backend
 */
function populateStats(user) {
    console.log('📊 Populating stat cards...');
    
    // User ID
    const statUserId = document.getElementById('statUserId');
    if (statUserId) {
        statUserId.textContent = user.user_id;
        console.log('  ✓ Set User ID:', user.user_id);
    }
    
    // Account Type (capitalize first letter)
    const statUserType = document.getElementById('statUserType');
    if (statUserType) {
        const userType = user.user_type
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
        statUserType.textContent = userType;
        console.log('  ✓ Set Account Type:', userType);
    }
    
    // Preferred Units (capitalize)
    const statUnits = document.getElementById('statUnits');
    if (statUnits) {
        const units = user.preferred_units.charAt(0).toUpperCase() + 
                     user.preferred_units.slice(1);
        statUnits.textContent = units;
        console.log('  ✓ Set Preferred Units:', units);
    }
    
    // Account Status
    const statStatus = document.getElementById('statStatus');
    if (statStatus) {
        const status = user.is_active ? 'Active ✅' : 'Inactive ❌';
        statStatus.textContent = status;
        statStatus.style.color = user.is_active ? '#10b981' : '#ef4444';
        console.log('  ✓ Set Account Status:', status);
    }
}

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
 */
function populateDataTable(user) {
    console.log('📋 Populating data table...');
    
    // User ID
    const dataUserId = document.getElementById('dataUserId');
    if (dataUserId) {
        dataUserId.textContent = user.user_id;
    }
    
    // Username
    const dataUsername = document.getElementById('dataUsername');
    if (dataUsername) {
        dataUsername.textContent = user.username;
    }
    
    // Email
    const dataEmail = document.getElementById('dataEmail');
    if (dataEmail) {
        dataEmail.textContent = user.email;
    }
    
    // Full Name
    const dataFullName = document.getElementById('dataFullName');
    if (dataFullName) {
        dataFullName.textContent = user.full_name || 'Not provided';
    }
    
    // User Type
    const dataUserType = document.getElementById('dataUserType');
    if (dataUserType) {
        const userType = user.user_type
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
        dataUserType.textContent = userType;
    }
    
    // Preferred Units
    const dataUnits = document.getElementById('dataUnits');
    if (dataUnits) {
        const units = user.preferred_units.charAt(0).toUpperCase() + 
                     user.preferred_units.slice(1);
        dataUnits.textContent = units;
    }
    
    // Account Created (format date)
    const dataCreated = document.getElementById('dataCreated');
    if (dataCreated) {
        const createdDate = new Date(user.created_at);
        dataCreated.textContent = formatDateTime(createdDate);
    }
    
    // Last Updated (format date)
    const dataUpdated = document.getElementById('dataUpdated');
    if (dataUpdated) {
        const updatedDate = new Date(user.updated_at);
        dataUpdated.textContent = formatDateTime(updatedDate);
    }
    
    console.log('  ✓ Data table populated');
}

/**
 * Display tokens for debugging
 * 
 * Shows:
 * - Access Token (JWT)
 * - Refresh Token (if available)
 * 
 * Note: Remove this in production for security!
 * 
 * @param {string} accessToken - JWT access token
 * @param {string} refreshToken - JWT refresh token (optional)
 */
function displayTokens() {
    console.log('🔑 Displaying tokens (DEBUG MODE)...');
    
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    const accessTokenEl = document.getElementById('accessToken');
    if (accessTokenEl) {
        if (accessToken) {
            accessTokenEl.textContent = accessToken;
        } else {
            accessTokenEl.textContent = 'Not available';
        }
    }
    
    const refreshTokenEl = document.getElementById('refreshToken');
    if (refreshTokenEl) {
        if (refreshToken) {
            refreshTokenEl.textContent = refreshToken;
        } else {
            refreshTokenEl.textContent = 'Not available';
        }
    }
    
    console.log('  ✓ Tokens displayed');
}

/**
 * Format date and time for display
 * 
 * Converts ISO date string to readable format:
 * "2025-11-06T10:30:00" → "November 6, 2025 at 10:30 AM"
 * 
 * @param {Date} date - Date object to format
 * @returns {string} Formatted date string
 */
function formatDateTime(date) {
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    
    return date.toLocaleString('en-US', options);
}

// ========================================
// STEP 4: HANDLE LOGOUT
// ========================================

/**
 * Setup logout button
 * 
 * Adds click handler to logout button that:
 * 1. Clears all stored data (tokens, user data)
 * 2. Redirects to login page
 */
function setupLogout() {
    console.log('🚪 Setting up logout button...');
    
    const logoutButton = document.getElementById('logoutButton');
    
    if (!logoutButton) {
        console.warn('⚠️ Logout button not found');
        return;
    }
    
    logoutButton.addEventListener('click', function() {
        console.log('👋 User clicked logout');
        
        // Show confirmation dialog
        const confirmed = confirm('Are you sure you want to logout?');
        
        if (confirmed) {
            console.log('✅ Logout confirmed');
            
            // Clear all authentication data
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            localStorage.removeItem('remember_me');
            
            console.log('🗑️ Cleared all stored data');
            
            // Redirect to login page
            console.log('🔄 Redirecting to login...');
            window.location.href = '/login.html';
        } else {
            console.log('❌ Logout cancelled');
        }
    });
    
    console.log('✅ Logout button setup complete');
}

// ========================================
// STEP 5: INITIALIZE DASHBOARD
// ========================================

/**
 * Initialize dashboard
 * 
 * Main function that orchestrates everything:
 * 1. Check authentication
 * 2. Fetch user data from backend
 * 3. Populate all dashboard sections
 * 4. Setup logout functionality
 * 
 * Called when DOM is ready
 */
async function initializeDashboard() {
    console.log('🚀 Initializing dashboard...');
    
    try {
        // Step 1: Check if user is authenticated
        if (!checkAuthentication()) {
            // User will be redirected to login
            return;
        }
        
        // Step 2: Fetch user data from backend
        console.log('📡 Fetching user data...');
        const userData = await fetchUserData();
        
        if (!userData) {
            console.error('❌ No user data received');
            return;
        }
        
        console.log('✅ User data fetched successfully:', userData);
        
        // Step 3: Populate dashboard sections
        populateHeader(userData);
        populateStats(userData);
        populateDataTable(userData);
        displayTokens();
        
        // Step 4: Setup logout button
        setupLogout();
        
        console.log('✨ Dashboard initialized successfully!');
        
    } catch (error) {
        console.error('💥 Error initializing dashboard:', error);
        
        // Show error message to user
        alert('Failed to load dashboard. Please try logging in again.');
        
        // Redirect to login
        window.location.href = '/login.html';
    }
}

// ========================================
// STEP 6: RUN WHEN PAGE LOADS
// ========================================

/**
 * Wait for DOM to be ready, then initialize dashboard
 * 
 * This ensures all HTML elements exist before we try to populate them
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM loaded, initializing dashboard...');
    initializeDashboard();
});

console.log('✅ dashboard.js loaded successfully');