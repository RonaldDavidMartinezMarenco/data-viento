/**
 * DataViento Landing Page - JavaScript
 * 
 * Features:
 * - Sticky navbar on scroll
 * - Mobile menu toggle
 * - Scroll animations
 * - Smooth scrolling
 */

// ========================================
// STICKY NAVBAR
// ========================================

const navbar = document.getElementById('navbar');
let lastScrollY = window.scrollY;

window.addEventListener('scroll', () => {
    const currentScrollY = window.scrollY;
    
    // Add 'scrolled' class when scrolling down
    if (currentScrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    lastScrollY = currentScrollY;
});

// ========================================
// MOBILE MENU TOGGLE
// ========================================

const navToggle = document.getElementById('nav-toggle');
const navMenu = document.getElementById('nav-menu');

if (navToggle) {
    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        navToggle.classList.toggle('active');
    });
}

// Close mobile menu when clicking on a link
const navLinks = document.querySelectorAll('.nav-link');

navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        navToggle.classList.remove('active');
    });
});

// ========================================
// SCROLL ANIMATIONS
// ========================================

const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animationPlayState = 'running';
            // Unobserve after animation starts (performance optimization)
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all elements with fade-in animations
const animatedElements = document.querySelectorAll('.fade-in-up, .fade-in');

animatedElements.forEach(el => {
    el.style.animationPlayState = 'paused';
    observer.observe(el);
});

// ========================================
// SMOOTH SCROLLING FOR ANCHOR LINKS
// ========================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        
        // Don't prevent default if href is just "#"
        if (href === '#') return;
        
        e.preventDefault();
        
        const target = document.querySelector(href);
        
        if (target) {
            const offsetTop = target.offsetTop - 80; // Account for fixed navbar
            
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// ========================================
// PARALLAX EFFECT FOR SHAPES
// ========================================

const shapes = document.querySelectorAll('.shape');

window.addEventListener('scroll', () => {
    const scrolled = window.scrollY;
    
    shapes.forEach((shape, index) => {
        const speed = 0.5 + (index * 0.2); // Different speeds for each shape
        const yPos = -(scrolled * speed);
        shape.style.transform = `translateY(${yPos}px)`;
    });
});

// ========================================
// CARD HOVER EFFECTS
// ========================================

const previewCards = document.querySelectorAll('.preview-card');

previewCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-8px) scale(1.02)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0) scale(1)';
    });
});

// ========================================
// FEATURE CARDS STAGGER ANIMATION
// ========================================

const featureCards = document.querySelectorAll('.feature-card');

const featureObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            setTimeout(() => {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }, index * 100); // Stagger by 100ms
            
            featureObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

featureCards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    featureObserver.observe(card);
});

// ========================================
// PERFORMANCE OPTIMIZATION
// ========================================

// Debounce function for scroll events
function debounce(func, wait = 10, immediate = true) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Log page load time (for performance monitoring)
window.addEventListener('load', () => {
    const loadTime = window.performance.timing.domContentLoadedEventEnd - 
                     window.performance.timing.navigationStart;
    console.log(`Page loaded in ${loadTime}ms`);
});

// ========================================
// ACCESSIBILITY
// ========================================

// Add focus-visible polyfill behavior
document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        document.body.classList.add('user-is-tabbing');
    }
});

document.addEventListener('mousedown', () => {
    document.body.classList.remove('user-is-tabbing');
});

// ========================================
// CONSOLE EASTER EGG
// ========================================

console.log('%cDataViento', 'font-size: 24px; font-weight: bold; color: #667eea;');
console.log('%cWeather intelligence for everyone', 'font-size: 14px; color: #8E8E93;');
console.log('%cPowered by Open-Meteo', 'font-size: 12px; color: #8E8E93;');
console.log('%cInterested in the code? Check out our GitHub:', 'font-size: 12px;');
console.log('%chttps://github.com/ronald-mendez/data-viento', 'font-size: 12px; color: #667eea;');