/**
 * Shared utility functions for RaiseMyHand
 * Common helpers used across student, instructor, and admin interfaces
 */

// ============================================================================
// API Key Management (Secure)
// ============================================================================

/**
 * Get API key from sessionStorage (more secure than localStorage)
 * @returns {string|null} The API key or null if not found
 */
function getApiKey() {
    // Use sessionStorage instead of localStorage for better security
    return sessionStorage.getItem('instructor_api_key');
}

/**
 * Set API key in sessionStorage
 * @param {string} apiKey - The API key to store
 */
function setApiKey(apiKey) {
    sessionStorage.setItem('instructor_api_key', apiKey);
}

/**
 * Clear API key from storage
 */
function clearApiKey() {
    sessionStorage.removeItem('instructor_api_key');
}

// ============================================================================
// CSRF Token Management
// ============================================================================

let cachedCsrfToken = null;
let csrfTokenExpiry = null;

/**
 * Get a CSRF token (cached for 30 minutes)
 * @returns {Promise<string>} The CSRF token
 */
async function getCsrfToken() {
    // Check if we have a valid cached token
    if (cachedCsrfToken && csrfTokenExpiry && Date.now() < csrfTokenExpiry) {
        return cachedCsrfToken;
    }

    // Fetch a new token
    try {
        const response = await fetch('/api/csrf-token');
        if (!response.ok) {
            throw new Error('Failed to fetch CSRF token');
        }
        const data = await response.json();
        cachedCsrfToken = data.csrf_token;
        // Cache for 30 minutes (token expires in 1 hour)
        csrfTokenExpiry = Date.now() + (30 * 60 * 1000);
        return cachedCsrfToken;
    } catch (error) {
        console.error('Error fetching CSRF token:', error);
        throw error;
    }
}

/**
 * Clear cached CSRF token (call on 403 errors)
 */
function clearCsrfToken() {
    cachedCsrfToken = null;
    csrfTokenExpiry = null;
}

/**
 * Get authorization headers with API key
 * @returns {Object} Headers object with Authorization bearer token
 */
function getAuthHeaders() {
    const apiKey = getApiKey();
    if (!apiKey) {
        return {};
    }
    return {
        'Authorization': `Bearer ${apiKey}`
    };
}

/**
 * Make authenticated fetch request with proper headers (including CSRF for POST/PUT/DELETE)
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
async function authenticatedFetch(url, options = {}) {
    const headers = {
        ...getAuthHeaders(),
        ...(options.headers || {})
    };

    // Add CSRF token for state-changing requests
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        try {
            const csrfToken = await getCsrfToken();
            headers['X-CSRF-Token'] = csrfToken;
        } catch (error) {
            console.error('Failed to get CSRF token:', error);
            // Continue without CSRF token - let the server reject it
        }
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    // If we get a 403, clear the CSRF token cache and try once more
    if (response.status === 403 && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        clearCsrfToken();
        // Optionally retry once with a fresh token
        // (commented out to avoid infinite loops)
        // const csrfToken = await getCsrfToken();
        // headers['X-CSRF-Token'] = csrfToken;
        // return fetch(url, { ...options, headers });
    }

    return response;
}

/**
 * Handle authentication errors
 */
function handleAuthError() {
    alert('Invalid or expired API key. Please enter a valid API key.');
    clearApiKey();
    promptForApiKey();
}

/**
 * Prompt user for API key
 */
function promptForApiKey() {
    const apiKey = prompt('Please enter your instructor API key:');
    if (apiKey) {
        setApiKey(apiKey);
        // Reload the page to retry with new key
        window.location.reload();
    } else {
        alert('API key is required to access instructor features.');
        window.location.href = '/';
    }
}

// ============================================================================
// Cookie Management
// ============================================================================

/**
 * Get a cookie value by name
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value or null
 */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

/**
 * Set a cookie
 * @param {string} name - Cookie name
 * @param {string} value - Cookie value
 * @param {number} days - Days until expiration
 */
function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Strict`;
}

// ============================================================================
// UI Utilities
// ============================================================================

/**
 * Display a notification to the user
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info)
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    // Auto-remove after 3 seconds with slide-out animation
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format a date/time string for display
 * @param {string} isoString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDateTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString();
}

/**
 * Format a relative time (e.g., "2 minutes ago")
 * @param {string} isoString - ISO date string
 * @returns {string} Relative time string
 */
function formatRelativeTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
}

// ============================================================================
// Upvote Management (Student)
// ============================================================================

/**
 * Check if user has upvoted a specific question
 * @param {string} sessionCode - Session code
 * @param {number} questionId - Question ID
 * @returns {boolean} True if upvoted
 */
function hasUpvoted(sessionCode, questionId) {
    const key = `upvoted_${sessionCode}`;
    const upvoted = JSON.parse(localStorage.getItem(key) || '[]');
    return upvoted.includes(questionId);
}

/**
 * Mark a question as upvoted
 * @param {string} sessionCode - Session code
 * @param {number} questionId - Question ID
 */
function markUpvoted(sessionCode, questionId) {
    const key = `upvoted_${sessionCode}`;
    const upvoted = JSON.parse(localStorage.getItem(key) || '[]');
    if (!upvoted.includes(questionId)) {
        upvoted.push(questionId);
        localStorage.setItem(key, JSON.stringify(upvoted));
    }
}

/**
 * Unmark a question as upvoted
 * @param {string} sessionCode - Session code
 * @param {number} questionId - Question ID
 */
function unmarkUpvoted(sessionCode, questionId) {
    const key = `upvoted_${sessionCode}`;
    const upvoted = JSON.parse(localStorage.getItem(key) || '[]');
    const index = upvoted.indexOf(questionId);
    if (index > -1) {
        upvoted.splice(index, 1);
        localStorage.setItem(key, JSON.stringify(upvoted));
    }
}

// ============================================================================
// Breadcrumb Navigation
// ============================================================================

/**
 * Create breadcrumb navigation
 * @param {Array} breadcrumbs - Array of {label, href} objects
 * @returns {HTMLElement} Breadcrumb navigation element
 */
function createBreadcrumbs(breadcrumbs) {
    const nav = document.createElement('nav');
    nav.className = 'breadcrumbs';
    nav.setAttribute('aria-label', 'Breadcrumb');

    const ol = document.createElement('ol');

    breadcrumbs.forEach((crumb, index) => {
        const li = document.createElement('li');

        if (index === breadcrumbs.length - 1) {
            // Last item (current page)
            const span = document.createElement('span');
            span.textContent = crumb.label;
            span.setAttribute('aria-current', 'page');
            li.appendChild(span);
        } else {
            // Link to previous pages
            const a = document.createElement('a');
            a.href = crumb.href;
            a.textContent = crumb.label;
            li.appendChild(a);
        }

        ol.appendChild(li);
    });

    nav.appendChild(ol);
    return nav;
}

/**
 * Add breadcrumbs to the page
 * @param {Array} breadcrumbs - Array of {label, href} objects
 * @param {string} containerId - ID of container to prepend breadcrumbs to (default: first .container)
 */
function addBreadcrumbs(breadcrumbs, containerId = null) {
    const breadcrumbNav = createBreadcrumbs(breadcrumbs);
    const container = containerId
        ? document.getElementById(containerId)
        : document.querySelector('.container');

    if (container) {
        container.insertBefore(breadcrumbNav, container.firstChild);
    }
}

// ============================================================================
// Loading States
// ============================================================================

/**
 * Show loading state on a button
 * @param {HTMLElement} button - Button element
 */
function showButtonLoading(button) {
    button.classList.add('loading');
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
}

/**
 * Hide loading state from a button
 * @param {HTMLElement} button - Button element
 */
function hideButtonLoading(button) {
    button.classList.remove('loading');
    button.disabled = false;
    button.removeAttribute('aria-busy');
}

/**
 * Show full-screen loading overlay
 * @param {string} message - Optional loading message
 * @returns {HTMLElement} Loading overlay element
 */
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loading-overlay';
    overlay.setAttribute('role', 'status');
    overlay.setAttribute('aria-live', 'polite');

    const spinner = document.createElement('div');
    spinner.className = 'spinner';

    const text = document.createElement('p');
    text.textContent = message;
    text.style.color = 'white';
    text.style.marginTop = '20px';
    text.style.fontSize = '18px';

    overlay.appendChild(spinner);
    overlay.appendChild(text);
    document.body.appendChild(overlay);

    return overlay;
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// ============================================================================
// Hamburger Menu Navigation
// ============================================================================

/**
 * Initialize hamburger menu functionality
 * Call this on pages that use the navigation
 */
function initHamburgerMenu() {
    const hamburger = document.getElementById('hamburger-btn');
    const navMenu = document.getElementById('nav-menu');
    const navOverlay = document.getElementById('nav-overlay');

    if (!hamburger || !navMenu) {
        return; // Navigation not present on this page
    }

    // Toggle menu
    function toggleMenu() {
        const isOpen = navMenu.classList.contains('open');
        navMenu.classList.toggle('open');
        if (navOverlay) {
            navOverlay.classList.toggle('open');
        }
        
        // Update ARIA attributes
        hamburger.setAttribute('aria-expanded', !isOpen);
        navMenu.setAttribute('aria-hidden', isOpen);
        
        // Prevent body scroll when menu is open
        document.body.style.overflow = isOpen ? '' : 'hidden';
    }

    // Hamburger button click
    hamburger.addEventListener('click', toggleMenu);

    // Overlay click to close
    if (navOverlay) {
        navOverlay.addEventListener('click', toggleMenu);
    }

    // Close button (the ::before pseudo-element acts as close)
    navMenu.addEventListener('click', (e) => {
        if (e.target === navMenu) {
            toggleMenu();
        }
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navMenu.classList.contains('open')) {
            toggleMenu();
        }
    });

    // Close menu when clicking nav links
    const navLinks = navMenu.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (navMenu.classList.contains('open')) {
                toggleMenu();
            }
        });
    });

    // Close menu on window resize to desktop
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.innerWidth > 768 && navMenu.classList.contains('open')) {
                toggleMenu();
            }
        }, 250);
    });
}

// Auto-initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHamburgerMenu);
} else {
    initHamburgerMenu();
}
