/**
 * DataViento - Register Page Logic
 */



console.log('register.js loaded');

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

const registerForm = document.getElementById('registerForm');
const usernameInput = document.getElementById('username');
const emailInput = document.getElementById('email');
const fullNameInput = document.getElementById('fullName');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const preferredUnitsSelect = document.getElementById('preferredUnits');
const termsCheckbox = document.getElementById('terms');
const registerButton = document.getElementById('registerButton');

// Password strength elements
const passwordStrengthContainer = document.getElementById('passwordStrength');
const passwordStrengthFill = document.getElementById('passwordStrengthFill');
const passwordStrengthText = document.getElementById('passwordStrengthText');


redirectIfAuthenticated();

// ========================================
// FORM VALIDATION
// ========================================

/**
 * Validate register form
 */
function validateRegisterForm() {
    let isValid = true;
    
    // Clear previous errors
    hideFormMessage('formError');
    hideFormMessage('formSuccess');
    clearFieldError('username');
    clearFieldError('email');
    clearFieldError('fullName');
    clearFieldError('password');
    clearFieldError('confirmPassword');
    clearFieldError('terms');
    
    // Validate username
    const username = usernameInput.value.trim();
    if (!username) {
        showFieldError('username', 'Username is required');
        isValid = false;
    } else if (!validateUsername(username)) {
        showFieldError('username', '3-50 characters, letters, numbers, and underscores only');
        isValid = false;
    } else {
        showFieldSuccess('username');
    }
    
    // Validate email
    const email = emailInput.value.trim();
    if (!email) {
        showFieldError('email', 'Email is required');
        isValid = false;
    } else if (!validateEmail(email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    } else {
        showFieldSuccess('email');
    }
    
    const password = passwordInput.value;
    if (!password) {
        showFieldError('password', 'Password is required');
        isValid = false;
    } else {
        const checks = validatePassword(password);
        
        // Check minimum length
        if (password.length < 8) {
            showFieldError('password', 'Password must be at least 8 characters');
            isValid = false;
        }
        // Check for uppercase letter (REQUIRED by Pydantic)
        else if (!checks.hasUpperCase) {
            showFieldError('password', 'Password must contain at least one uppercase letter (A-Z)');
            isValid = false;
        }
        // Check for lowercase letter (REQUIRED by Pydantic)
        else if (!checks.hasLowerCase) {
            showFieldError('password', 'Password must contain at least one lowercase letter (a-z)');
            isValid = false;
        }
        // Check for number (REQUIRED by Pydantic)
        else if (!checks.hasNumber) {
            showFieldError('password', 'Password must contain at least one number (0-9)');
            isValid = false;
        }
        // Password meets all requirements
        else {
            const strength = getPasswordStrength(password);
            
            // Only allow submission if password is medium or strong
            if (strength === 'weak') {
                showFieldError('password', 'Password is too weak. Please add more variety');
                isValid = false;
            } else {
                showFieldSuccess('password');
            }
        }
    }
    
    // Validate confirm password
    const confirmPassword = confirmPasswordInput.value;
    if (!confirmPassword) {
        showFieldError('confirmPassword', 'Please confirm your password');
        isValid = false;
    } else if (password !== confirmPassword) {
        showFieldError('confirmPassword', 'Passwords do not match');
        isValid = false;
    } else {
        showFieldSuccess('confirmPassword');
    }
    
    // Validate terms
    if (!termsCheckbox.checked) {
        showFieldError('terms', 'You must agree to the Terms of Service and Privacy Policy');
        isValid = false;
    }
    
    return isValid;
}

// ========================================
// PASSWORD STRENGTH INDICATOR
// ========================================

/**
 * Update password strength indicator with detailed feedback
 */
function updatePasswordStrength() {
    const password = passwordInput.value;
    
    if (!password) {
        passwordStrengthContainer.style.display = 'none';
        return;
    }
    
    passwordStrengthContainer.style.display = 'block';
    
    const checks = validatePassword(password);
    
    // ✅ UPDATED: More detailed strength calculation
    let score = 0;
    let missingRequirements = [];
    
    // Required checks (matching Pydantic model)
    if (checks.length) score++; else missingRequirements.push('8+ characters');
    if (checks.hasUpperCase) score++; else missingRequirements.push('uppercase (A-Z)');
    if (checks.hasLowerCase) score++; else missingRequirements.push('lowercase (a-z)');
    if (checks.hasNumber) score++; else missingRequirements.push('number (0-9)');
    
    // Optional but recommended
    if (checks.hasSpecialChar) score++;
    
    // Determine strength
    let strength, strengthText, tipText;
    
    if (score < 4) {
        // Missing required fields - WEAK (cannot submit)
        strength = 'weak';
        strengthText = '❌ Weak password';
        tipText = ' - Missing: ' + missingRequirements.join(', ');
    } else if (score === 4) {
        // Has all required fields but no special char - MEDIUM (can submit)
        strength = 'medium';
        strengthText = '⚠️ Medium password';
        tipText = ' - Add special characters (!@#$%^&*) for stronger security';
    } else {
        // Has all requirements + special char - STRONG (can submit)
        strength = 'strong';
        strengthText = '✅ Strong password';
        tipText = ' - Excellent!';
    }
    

    passwordStrengthFill.className = 'password-strength-fill ' + strength;
    
    passwordStrengthText.textContent = strengthText + tipText;
    passwordStrengthText.className = 'password-strength-text ' + strength;
    
    updateSubmitButtonState();
}


function updateSubmitButtonState() {
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    
    if (!password) {
        registerButton.disabled = false;
        return;
    }
    
    const checks = validatePassword(password);
    const hasAllRequired = 
        password.length >= 8 &&
        checks.hasUpperCase &&
        checks.hasLowerCase &&
        checks.hasNumber;
    
    const passwordsMatch = password === confirmPassword;
    
    // Disable if password doesn't meet requirements or passwords don't match
    if (!hasAllRequired || (confirmPassword && !passwordsMatch)) {
        registerButton.disabled = true;
        registerButton.style.opacity = '0.6';
        registerButton.style.cursor = 'not-allowed';
        registerButton.title = 'Please fix password requirements';
    } else {
        registerButton.disabled = false;
        registerButton.style.opacity = '1';
        registerButton.style.cursor = 'pointer';
        registerButton.title = '';
    }
}

// ========================================
// FORM SUBMISSION
// ========================================

/**
 * Handle register form submission
 */
async function handleRegister(e) {
    e.preventDefault();
    
    // Validate form
    if (!validateRegisterForm()) {
        return;
    }
    
    // Get form data
    const userData = {
        username: usernameInput.value.trim(),
        email: emailInput.value.trim(),
        password: passwordInput.value,
        preferred_units: preferredUnitsSelect.value
    };
    
    // Add full name if provided
    const fullName = fullNameInput.value.trim();
    if (fullName) {
        userData.full_name = fullName;
    }
    
    // Set loading state
    setButtonLoading('registerButton', true);
    hideFormMessage('formError');
    hideFormMessage('formSuccess');
    
    try {
        // Call register API
        const response = await registerUser(userData);
        
        console.log('✅ Registration successful:', response);
        
        // Show success message
        showFormMessage(
            'formSuccess',
            'Account created successfully! Redirecting to login...',
            'success'
        );
        
        // Redirect to login after 2 seconds
        setTimeout(() => {
            window.location.href = '/login.html?registered=true';
        }, 2000);
        
    } catch (error) {
        console.error('❌ Registration error:', error);
        
        // Show error message
        let errorMessage = 'An error occurred. Please try again.';
        
        if (error.status === 400) {
            // Handle validation errors
            if (error.message.includes('username')) {
                errorMessage = 'Username already exists. Please choose another one.';
                showFieldError('username', 'This username is already taken');
            } else if (error.message.includes('email')) {
                errorMessage = 'Email already exists. Please use another email.';
                showFieldError('email', 'This email is already registered');
            } else {
                errorMessage = error.message;
            }
        } else if (error.status === 422) {
            errorMessage = 'Please check your input and try again.';
            
            // Show field-specific errors if available
            if (error.fullError && error.fullError.detail) {
                console.log('📋 Validation errors:', error.fullError.detail);
                
                if (Array.isArray(error.fullError.detail)) {
                    error.fullError.detail.forEach(err => {
                        const field = err.loc?.[1] || err.loc?.[0];
                        const message = err.msg || 'Invalid value';
                        
                        console.log(`  Field: ${field}, Error: ${message}`);
                        
                        if (field === 'password') {
                            showFieldError('password', message);
                            errorMessage = 'Password does not meet requirements';
                        } else if (field) {
                            showFieldError(field, message);
                        }
                    });
                }
            }
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        showFormMessage('formError', errorMessage, 'error');
        
    } finally {
        // Reset loading state
        setButtonLoading('registerButton', false);
    }
}

// ========================================
// REAL-TIME VALIDATION
// ========================================

/**
 * Setup real-time validation
 */
function setupRealtimeValidation() {
    // Username validation
    usernameInput.addEventListener('blur', function() {
        const username = this.value.trim();
        
        if (!username) {
            showFieldError('username', 'Username is required');
        } else if (!validateUsername(username)) {
            showFieldError('username', '3-50 characters, letters, numbers, and underscores only');
        } else {
            clearFieldError('username');
            showFieldSuccess('username');
        }
    });
    
    usernameInput.addEventListener('input', function() {
        if (this.value.trim()) {
            clearFieldError('username');
        }
    });
    
    // Email validation
    emailInput.addEventListener('blur', function() {
        const email = this.value.trim();
        
        if (!email) {
            showFieldError('email', 'Email is required');
        } else if (!validateEmail(email)) {
            showFieldError('email', 'Please enter a valid email address');
        } else {
            clearFieldError('email');
            showFieldSuccess('email');
        }
    });
    
    emailInput.addEventListener('input', function() {
        if (this.value.trim()) {
            clearFieldError('email');
        }
    });
    
    // ✅ UPDATED: Password validation with strength indicator and button state
    passwordInput.addEventListener('input', function() {
        updatePasswordStrength();
        clearFieldError('password');
        
        // Re-validate confirm password if it has a value
        if (confirmPasswordInput.value) {
            validateConfirmPassword();
        }
    });
    
    passwordInput.addEventListener('blur', function() {
        const password = this.value;
        
        if (!password) {
            showFieldError('password', 'Password is required');
            passwordStrengthContainer.style.display = 'none';
            updateSubmitButtonState();
        }
    });
    
    // Confirm password validation
    confirmPasswordInput.addEventListener('input', function() {
        validateConfirmPassword();
        updateSubmitButtonState();
    });
    
    confirmPasswordInput.addEventListener('blur', function() {
        validateConfirmPassword();
    });
    
    // Terms checkbox
    termsCheckbox.addEventListener('change', function() {
        if (this.checked) {
            clearFieldError('terms');
        }
    });
}

/**
 * Validate confirm password field
 */
function validateConfirmPassword() {
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    
    clearFieldError('confirmPassword');
    
    if (!confirmPassword) {
        // Don't show error if field is empty
        return;
    }
    
    if (password !== confirmPassword) {
        showFieldError('confirmPassword', 'Passwords do not match');
    } else {
        showFieldSuccess('confirmPassword');
    }
}

// ========================================
// KEYBOARD SHORTCUTS
// ========================================

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    // Submit form on Enter key
    registerForm.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !registerButton.disabled) {
            // Only submit if not in a textarea or if Ctrl+Enter is pressed
            if (e.target.tagName !== 'TEXTAREA' || e.ctrlKey) {
                handleRegister(e);
            }
        }
    });
}

// ========================================
// SUCCESS MESSAGE FROM LOGIN PAGE
// ========================================

/**
 * Show success message if redirected from login
 */
function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Show message if coming from a successful action
    if (urlParams.get('registered') === 'true') {
        showFormMessage(
            'formSuccess',
            'Registration successful! Please log in with your credentials.',
            'success'
        );
    }
}

// ========================================
// INITIALIZE
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Setup form submission
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Setup real-time validation
    setupRealtimeValidation();

    setupPasswordToggles();
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Check URL parameters
    checkUrlParams();
    
    // Focus on username field
    if (usernameInput) {
        usernameInput.focus();
    }
    
    console.log('✅ Register page initialized');
});