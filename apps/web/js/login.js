/**
 * Login Page JavaScript
 */

console.log('login.js loaded');

// Check if AuthUtils exists
if (!window.AuthUtils) {
    console.error('FATAL: AuthUtils not loaded!');
    alert('Error: Authentication utilities not loaded. Please refresh the page.');
} else {
    console.log('AuthUtils loaded successfully');
}


// ========================================
// DOM ELEMENTS
// ========================================

const loginForm = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const rememberMeCheckbox = document.getElementById('remember');



// ========================================
// FORM VALIDATION
// ========================================

/**
 * Validate login form
 */
function validateLoginForm(credentials) {
    let isValid = true;
    
    hideFormMessages();
    
    if (!credentials.username || credentials.username.trim() === '') {
        showFieldError('username', 'Username or email is required');
        isValid = false;
    }
    
    if (!credentials.password || credentials.password.trim() === '') {
        showFieldError('password', 'Password is required');
        isValid = false;
    }
    
    return isValid;
}

// ========================================
// LOGIN HANDLER
// ========================================

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    console.log('🚀 Login form submitted');
    
    e.preventDefault();
    e.stopPropagation();
    
    const credentials = {
        username: usernameInput.value.trim(),
        password: passwordInput.value
    };
    
    console.log('📝 Credentials:', {
        username: credentials.username,
        password: '***HIDDEN***'
    });
    
    // Validate
    if (!validateLoginForm(credentials)) {
        console.log('❌ Validation failed');
        return;
    }
    
    console.log('✅ Validation passed');
    
    setButtonLoading('loginButton', true);
    hideFormMessages();
    
    try {
        const apiUrl = getApiUrl(API_CONFIG.endpoints.login);
        console.log('📡 API URL:', apiUrl);
        console.log('📤 Sending POST request...');
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials)
        });
        
        console.log('📥 Response status:', response.status);
        
        const data = await response.json();
        console.log('📦 Response data:', data);
        
        if (!response.ok) {
            console.error('❌ Login failed:', data);
            
            let errorMessage = 'Login failed. Please try again.';
            
            if (response.status === 401) {
                errorMessage = 'Invalid username or password';
            } else if (response.status === 422) {
                errorMessage = 'Invalid request format';
            } else if (data.detail) {
                errorMessage = data.detail;
            }
            
            throw new Error(errorMessage);
        }
        
        console.log('🎉 LOGIN SUCCESS!');
        console.log('👤 User:', data.user);
        console.log('🔑 Access token:', data.access_token ? 'Received' : 'Missing');
        console.log('🔑 Refresh token:', data.refresh_token ? 'Received' : 'Missing');
        
        // Store tokens and user data
        storeTokens(data.access_token, data.refresh_token);
        storeUserData(data.user);
        
        console.log('💾 Data stored in localStorage');
        
        // Handle "Remember Me"
        if (rememberMeCheckbox && rememberMeCheckbox.checked) {
            localStorage.setItem('remember_me', 'true');
            console.log('✅ Remember me enabled');
        }
        
        showFormSuccess('Login successful! Redirecting...');
        
        // Redirect to dashboard after 1 second
        setTimeout(() => {
            console.log('🔄 Redirecting to dashboard...');
            window.location.href = '/dashboard.html'; // ✅ Changed to dashboard
        }, 1000);
        
    } catch (error) {
        console.error('💥 Login error:', error);
        showFormError(error.message);
    } finally {
        setButtonLoading('loginButton', false);
    }
}

// ========================================
// EVENT LISTENERS
// ========================================

if (loginForm) {
    console.log('✅ Attaching submit listener to form');
    loginForm.addEventListener('submit', handleLogin);
    console.log('✅ Event listener attached');
} else {
    console.error('❌ CRITICAL: loginForm element not found!');
}

// Handle Enter key
if (usernameInput) {
    usernameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            passwordInput.focus();
        }
    });
}

if (passwordInput) {
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            loginForm.dispatchEvent(new Event('submit'));
        }
    });
}

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Login page initializing...');
    
    setupPasswordToggles()
    
    // Clear errors on input
    if (loginForm) {
        const inputs = loginForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                clearFieldError(input.id);
                hideFormMessages();
            });
        });
    }
    
    // Check if redirected from registration
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('registered') === 'true') {
        showFormSuccess('Registration successful! Please log in.');
    }
    
    console.log('✅ Login page initialized');
});