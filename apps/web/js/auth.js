/**
 * DataViento - Shared Authentication Utilities
 * 
 * This file contains shared functions and configurations
 * used across both login and register pages
 */

// ========================================
// CONFIGURATION
// ========================================

const API_CONFIG = {
    // Update this to your backend URL
    baseURL: 'http://localhost:8000',
    endpoints: {
        login: '/auth/login',
        register: '/auth/register',
        logout: '/auth/logout',
        refresh: '/auth/refresh',
        verify: '/auth/verify',
        me: '/users/me'
    }
};

// ========================================
// API HELPER FUNCTIONS
// ========================================

/**
 * Get full API URL
 */
function getApiUrl(endpoint) {
    const url = `${API_CONFIG.baseURL}${endpoint}`;
    // Remove double slashes (except after http://)
    return url.replace(/([^:]\/)\/+/g, "$1");
}

/**
 * Make API request
 */
async function apiRequest(endpoint, options = {}) {
    const url = getApiUrl(endpoint);
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    // Add auth token if it exists
    const token = localStorage.getItem('access_token');
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };
    
    try {
        console.log('📡 API Request:', {
            url,
            method: config.method || 'GET',
            headers: config.headers,
            body : options.body
        });
        
        const response = await fetch(url, config);
        
        // ✅ FIX #2: Changed = to () for proper function call
        console.log('📥 API Response:', {
            status: response.status,
            statusText: response.statusText,
            headers:{
                'content-type':response.headers.get('content-type')
            }
        });
        
        
        
        let data;
        try {
            data = await response.json();
            console.log('📦 Response Data:', data); // ✅ Add this to see full response
        } catch (parseError) {
            console.error('❌ Failed to parse response as JSON:', parseError);
            throw {
                status: response.status,
                message: 'Invalid response from server',
                errors: null
            };
        }
        
        if (!response.ok) {
            console.error('❌ Request failed with error:', data); // ✅ Log full error
            throw {
                status: response.status,
                message: data.detail || data.message || 'An error occurred',
                errors: data.errors || data.validation_errors || null, // ✅ Try both field names
                fullError: data // ✅ Include full error for debugging
            };
        }
        
        return data;
        
    } catch (error) {
        console.error('💥 API Error:', error);
        
        // Network error or parsing error
        if (!error.status) {
            throw {
                status: 0,
                message: 'Network error. Please check your connection.',
                errors: null
            };
        }
        throw error;
    }
}

/**
 * Login user
 */
async function loginUser(username, password) {
    console.log('🔐 Logging in user:', username);
    
    // ✅ FIX #1: Changed json to JSON (uppercase)
    return await apiRequest(API_CONFIG.endpoints.login, {
        method: 'POST',
        body: JSON.stringify({ username: username, password: password })
    });
}

/**
 * Register user
 */
async function registerUser(userData) {
    console.log('📝 Registering user:', { ...userData, password: '***' });
    
    return await apiRequest(API_CONFIG.endpoints.register, {
        method: 'POST',
        body: JSON.stringify(userData)
    });
}

/**
 * Get current user
 */
async function getCurrentUser() {
    return await apiRequest(API_CONFIG.endpoints.me, {
        method: 'GET'
    });
}

/**
 * Logout user
 */
function logoutUser() {
    console.log('🚪 Logging out user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

// ========================================
// TOKEN MANAGEMENT
// ========================================

/**
 * Store auth tokens
 */
function storeTokens(accessToken, refreshToken) {
    console.log('💾 Storing tokens');
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
    }
}

/**
 * Store auth token (legacy - use storeTokens)
 */
function storeToken(token) {
    localStorage.setItem('access_token', token);
}

/**
 * Get auth token
 */
function getToken() {
    return localStorage.getItem('access_token');
}

/**
 * Get auth token (alias)
 */
function getAuthToken() {
    return getToken();
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getToken();
}

/**
 * Store user data
 */
function storeUser(user) {
    console.log('💾 Storing user data:', user);
    localStorage.setItem('user', JSON.stringify(user));
}

/**
 * Store user data (alias)
 */
function storeUserData(user) {
    storeUser(user);
}

/**
 * Get user data
 */
function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

/**
 * Get user data (alias)
 */
function getUserData() {
    return getUser();
}

/**
 * Clear all auth data
 */
function clearAuthData() {
    console.log('🗑️ Clearing all auth data');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('remember_me');
}

// ========================================
// FORM VALIDATION UTILITIES
// ========================================

/**
 * Validate email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate username
 */
function validateUsername(username) {
    // 3-50 characters, letters, numbers, and underscores only
    const re = /^[a-zA-Z0-9_]{3,50}$/;
    return re.test(username);
}

/**
 * Validate password strength
 */
function validatePassword(password) {
    return {
        length: password.length >= 8,
        hasUpperCase: /[A-Z]/.test(password),
        hasLowerCase: /[a-z]/.test(password),
        hasNumber: /[0-9]/.test(password),
        hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
}

/**
 * Get password strength score
 */
function getPasswordStrength(password) {
    const checks = validatePassword(password);
    let score = 0;
    
    if (checks.length) score++;
    if (checks.hasUpperCase) score++;
    if (checks.hasLowerCase) score++;
    if (checks.hasNumber) score++;
    if (checks.hasSpecialChar) score++;
    
    if (score <= 2) return 'weak';
    if (score <= 4) return 'medium';
    return 'strong';
}

// ========================================
// UI HELPER FUNCTIONS
// ========================================

/**
 * Show form error
 */
function showFieldError(fieldId, message) {
    const input = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}-error`);
    
    if (input) {
        input.classList.add('error');
        input.classList.remove('success');
    }
    
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('active');
    }
}

/**
 * Clear field error
 */
function clearFieldError(fieldId) {
    const input = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}-error`);
    
    if (input) {
        input.classList.remove('error');
    }
    
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.classList.remove('active');
    }
}

/**
 * Show field success
 */
function showFieldSuccess(fieldId) {
    const input = document.getElementById(fieldId);
    
    if (input) {
        input.classList.remove('error');
        input.classList.add('success');
    }
    
    clearFieldError(fieldId);
}

/**
 * Show form message
 */
function showFormMessage(messageId, text, type = 'error') {
    const messageElement = document.getElementById(messageId);
    const textElement = messageElement?.querySelector('span');
    
    if (messageElement && textElement) {
        textElement.textContent = text;
        messageElement.style.display = 'flex';
        
        // Auto-hide after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 5000);
        }
    }
}

/**
 * Show form success message
 */
function showFormSuccess(message) {
    showFormMessage('formSuccess', message, 'success');
}

/**
 * Show form error message
 */
function showFormError(message) {
    showFormMessage('formError', message, 'error');
}

/**
 * Hide form message
 */
function hideFormMessage(messageId) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.style.display = 'none';
    }
}

/**
 * Hide all form messages
 */
function hideFormMessages() {
    hideFormMessage('formError');
    hideFormMessage('formSuccess');
}

/**
 * Set button loading state
 */
function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');
    
    if (isLoading) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'inline-flex';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
    }
}

// ========================================
// PASSWORD TOGGLE FUNCTIONALITY
// ========================================
// ✅ FIXED: Track if already initialized to prevent duplicates
let passwordTogglesInitialized = false;

function setupPasswordToggles() {
    // ✅ Prevent duplicate initialization
    if (passwordTogglesInitialized) {
        console.log('⚠️ Password toggles already initialized, skipping...');
        return;
    }
    
    const toggleButtons = document.querySelectorAll('.form-input-toggle');
    
    console.log('🔧 Setting up password toggles:', toggleButtons.length);
    
    if (toggleButtons.length === 0) {
        console.warn('⚠️ No toggle buttons found');
        return;
    }
    
    toggleButtons.forEach((button, index) => {
        const showIcon = button.querySelector('.toggle-show');
        const hideIcon = button.querySelector('.toggle-hide');
        
        if (!showIcon || !hideIcon) {
            console.error(`❌ Toggle ${index + 1}: Missing icons`);
            return;
        }
        
        // ✅ Set initial state (password hidden, show eye icon)
        showIcon.style.display = 'block';
        showIcon.style.visibility = 'visible';
        showIcon.style.opacity = '1';
        
        hideIcon.style.display = 'none';
        hideIcon.style.visibility = 'hidden';
        hideIcon.style.opacity = '0';
        
        button.classList.remove('active');
        
        console.log(`  ✅ Toggle ${index + 1} initialized`);
        
        // ✅ Add click listener only once
        button.addEventListener('click', function togglePassword(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const wrapper = this.parentElement;
            const input = wrapper.querySelector('input[type="password"], input[type="text"]');
            
            if (!input) {
                console.error('❌ No input found for toggle button');
                return;
            }
            
            const showIcon = this.querySelector('.toggle-show');
            const hideIcon = this.querySelector('.toggle-hide');
            
            // Toggle password visibility
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            
            // Toggle icons
            if (isPassword) {
                // Password now visible - show eye-off icon
                showIcon.style.display = 'none';
                showIcon.style.visibility = 'hidden';
                showIcon.style.opacity = '0';
                
                hideIcon.style.display = 'block';
                hideIcon.style.visibility = 'visible';
                hideIcon.style.opacity = '1';
                
                this.classList.add('active');
                console.log('  👁️ Password visible');
            } else {
                // Password now hidden - show eye icon
                showIcon.style.display = 'block';
                showIcon.style.visibility = 'visible';
                showIcon.style.opacity = '1';
                
                hideIcon.style.display = 'none';
                hideIcon.style.visibility = 'hidden';
                hideIcon.style.opacity = '0';
                
                this.classList.remove('active');
                console.log('  🔒 Password hidden');
            }
            
            input.focus();
        });
    });
    
    passwordTogglesInitialized = true;
    console.log('✅ Password toggles setup complete');
}

function togglePasswordVisibility(inputId, toggleId) {
    const input = document.getElementById(inputId);
    const toggle = document.getElementById(toggleId);
    
    if (!input || !toggle) {
        console.warn('⚠️ togglePasswordVisibility: Elements not found', { inputId, toggleId });
        return;
    }
    
    toggle.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        
        if (isPassword) {
            this.classList.add('active');
        } else {
            this.classList.remove('active');
        }
        
        input.focus();
    });
}


// ========================================
// REDIRECT HANDLING
// ========================================

/**
 * Redirect to dashboard if already authenticated
 */
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        console.log('✅ User already authenticated, redirecting to dashboard');
        window.location.href = '/dashboard.html';
    }
}

/**
 * Redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        console.log('⚠️ User not authenticated, redirecting to login');
        window.location.href = '/login.html';
    }
}

/**
 * Redirect to login page
 */
function redirectToLogin() {
    window.location.href = '/login.html';
}

/**
 * Redirect to dashboard
 */
function redirectToDashboard() {
    window.location.href = '/dashboard.html';
}

// ========================================
// INITIALIZE
// ========================================


// ========================================
// EXPORT TO WINDOW (FOR BROWSER USAGE)
// ========================================

// Make all functions available globally via window.AuthUtils
window.AuthUtils = {
    // Config
    API_CONFIG,
    
    // API functions
    getApiUrl,
    apiRequest,
    loginUser,
    registerUser,
    getCurrentUser,
    logoutUser,
    
    // Token management
    storeTokens,
    storeToken,
    getToken,
    getAuthToken,
    isAuthenticated,
    
    // User data
    storeUser,
    storeUserData,
    getUser,
    getUserData,
    clearAuthData,
    
    // Validation
    validateEmail,
    validateUsername,
    validatePassword,
    getPasswordStrength,
    
    // UI helpers
    showFieldError,
    clearFieldError,
    showFieldSuccess,
    showFormMessage,
    showFormSuccess,
    showFormError,
    hideFormMessage,
    hideFormMessages,
    setButtonLoading,
    
    // Password toggle
    setupPasswordToggles,
    togglePasswordVisibility,
    
    // Redirect
    redirectIfAuthenticated,
    requireAuth,
    redirectToLogin,
    redirectToDashboard
};

// Also export as global functions (for backward compatibility)
if (typeof window !== 'undefined') {
    // API functions
    window.getApiUrl = getApiUrl;
    window.apiRequest = apiRequest;
    window.loginUser = loginUser;
    window.registerUser = registerUser;
    window.getCurrentUser = getCurrentUser;
    window.logoutUser = logoutUser;
    
    // Token management
    window.storeTokens = storeTokens;
    window.storeToken = storeToken;
    window.getToken = getToken;
    window.getAuthToken = getAuthToken;
    window.isAuthenticated = isAuthenticated;
    
    // User data
    window.storeUser = storeUser;
    window.storeUserData = storeUserData;
    window.getUser = getUser;
    window.getUserData = getUserData;
    window.clearAuthData = clearAuthData;
    
    // Validation
    window.validateEmail = validateEmail;
    window.validateUsername = validateUsername;
    window.validatePassword = validatePassword;
    window.getPasswordStrength = getPasswordStrength;
    
    // UI helpers
    window.showFieldError = showFieldError;
    window.clearFieldError = clearFieldError;
    window.showFieldSuccess = showFieldSuccess;
    window.showFormMessage = showFormMessage;
    window.showFormSuccess = showFormSuccess;
    window.showFormError = showFormError;
    window.hideFormMessage = hideFormMessage;
    window.hideFormMessages = hideFormMessages;
    window.setButtonLoading = setButtonLoading;
    
    // Password toggle
    window.setupPasswordToggles = setupPasswordToggles;
    window.togglePasswordVisibility = togglePasswordVisibility;
    
    // Redirect
    window.redirectIfAuthenticated = redirectIfAuthenticated;
    window.requireAuth = requireAuth;
    window.redirectToLogin = redirectToLogin;
    window.redirectToDashboard = redirectToDashboard;
}

console.log('✅ auth.js loaded - All functions exported globally');