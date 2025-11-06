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
    e.preventDefault();
    
    console.log('🚀 Login form submitted');
    
    // Get form values
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    const rememberMe = rememberMeCheckbox.checked;
    
    console.log('📝 Credentials:', { 
        username, 
        password: '***HIDDEN***', 
        rememberMe 
    });
    
    // Basic validation
    if (!username || !password) {
        showFormError('Please enter both username and password');
        return;
    }
    
    console.log('✅ Validation passed');
    
    // Set loading state
    setButtonLoading('loginButton', true);
    hideFormMessages();
    
    try {
        console.log('📡 Calling loginUser...');
        
        // Call login API
        const response = await loginUser(username, password);
        
        console.log('🎉 LOGIN SUCCESS!');
        console.log('📦 Response:', response);
        
        // ✅ UPDATED: Store tokens
        if (response.access_token) {
            console.log('🔑 Access token:', response.access_token.substring(0, 20) + '...');
            storeToken(response.access_token);
        }
        
        if (response.refresh_token) {
            console.log('🔑 Refresh token:', response.refresh_token.substring(0, 20) + '...');
            localStorage.setItem('refresh_token', response.refresh_token);
        }
        
        // ✅ UPDATED: Store complete user data from response
        if (response.user) {
            console.log('👤 User:', response.user);
            storeUser(response.user);
        }
        
        // Store remember me preference
        if (rememberMe) {
            localStorage.setItem('remember_me', 'true');
            console.log('✅ Remember me enabled');
        }
        
        console.log('💾 Data stored in localStorage');
        
        // Show success message
        showFormSuccess('Login successful! Redirecting...');
        
        // Redirect to dashboard after short delay
        console.log('🔄 Redirecting to dashboard...');
        setTimeout(() => {
            window.location.href = '/dashboard.html';
        }, 1000);
        
    } catch (error) {
        console.error('❌ Login failed:', error);
        
        let errorMessage = 'An error occurred. Please try again.';
        
        if (error.status === 401) {
            errorMessage = 'Invalid username or password';
        } else if (error.status === 403) {
            errorMessage = 'Your account has been disabled';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        showFormError(errorMessage);
        
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