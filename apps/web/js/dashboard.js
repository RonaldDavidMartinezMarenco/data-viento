/**
 * Dashboard Page JavaScript
 */

console.log('📊 Dashboard.js loaded');


// ========================================
// CHECK AUTHENTICATION
// ========================================

/**
 * Check if user is authenticated
 * Redirect to login if not
 */
function checkAuth() {
    const user = getUserData();
    const token = getAuthToken();
    
    console.log('🔐 Checking authentication...');
    console.log('User data:', user);
    console.log('Token:', token ? 'Present' : 'Missing');
    
    if (!user || !token) {
        console.warn('⚠️ Not authenticated, redirecting to login...');
        window.location.href = '/login.html';
        return false;
    }
    
    console.log('✅ User is authenticated');
    return true;
}

// ========================================
// POPULATE USER DATA
// ========================================

/**
 * Populate dashboard with user data
 */
function populateUserData() {
    const user = getUserData();
    
    if (!user) {
        console.error('❌ No user data found');
        return;
    }
    
    console.log('📝 Populating user data:', user);
    
    // Get user initials
    const initials = user.full_name 
        ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()
        : user.username.substring(0, 2).toUpperCase();
    
    // Header
    document.getElementById('userInitials').textContent = initials;
    document.getElementById('userName').textContent = user.full_name || user.username;
    document.getElementById('userEmail').textContent = user.email;
    
    // Welcome
    document.getElementById('welcomeName').textContent = user.full_name || user.username;
    
    // Stats Cards
    document.getElementById('statUserId').textContent = user.user_id;
    document.getElementById('statUserType').textContent = formatUserType(user.user_type);
    document.getElementById('statUnits').textContent = formatUnits(user.preferred_units);
    document.getElementById('statStatus').textContent = user.is_active ? '✅ Active' : '❌ Inactive';
    
    // Data Table
    document.getElementById('dataUserId').textContent = user.user_id;
    document.getElementById('dataUsername').textContent = user.username;
    document.getElementById('dataEmail').textContent = user.email;
    document.getElementById('dataFullName').textContent = user.full_name || 'Not provided';
    document.getElementById('dataUserType').textContent = formatUserType(user.user_type);
    document.getElementById('dataUnits').textContent = formatUnits(user.preferred_units);
    document.getElementById('dataCreated').textContent = formatDate(user.created_at);
    document.getElementById('dataUpdated').textContent = formatDate(user.updated_at);
    
    // Tokens
    const accessToken = getAuthToken();
    const refreshToken = localStorage.getItem('refresh_token');
    
    document.getElementById('accessToken').textContent = accessToken || 'Not found';
    document.getElementById('refreshToken').textContent = refreshToken || 'Not found';
    
    console.log('✅ User data populated');
}

// ========================================
// HELPER FUNCTIONS
// ========================================

/**
 * Format user type for display
 */
function formatUserType(userType) {
    const types = {
        'standard_user': 'Standard User',
        'premium_user': 'Premium User',
        'admin': 'Administrator'
    };
    return types[userType] || userType;
}

/**
 * Format units for display
 */
function formatUnits(units) {
    const unitTypes = {
        'metric': 'Metric (°C, km/h, mm)',
        'imperial': 'Imperial (°F, mph, in)'
    };
    return unitTypes[units] || units;
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

// ========================================
// LOGOUT HANDLER
// ========================================

/**
 * Handle logout
 */
function handleLogout() {
    console.log('🚪 Logging out...');
    
    if (confirm('Are you sure you want to logout?')) {
        // Clear tokens and user data
        clearAuthData();
        
        console.log('✅ Auth data cleared');
        
        // Redirect to login
        window.location.href = '/login.html';
    }
}

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');
    
    // Check authentication
    if (!checkAuth()) {
        return; // Will redirect to login
    }
    
    // Populate user data
    populateUserData();
    
    // Setup logout button
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
        console.log('✅ Logout button attached');
    }
    
    console.log('✅ Dashboard initialized successfully');
});