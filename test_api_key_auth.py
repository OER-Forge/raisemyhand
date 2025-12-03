#!/usr/bin/env python3
"""
Test script for API Key authentication flow
Tests Phase 1 fixes for localStorage -> sessionStorage migration
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_test(test_name, passed, message=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} - {test_name}")
    if message:
        print(f"       {message}")

def test_admin_login():
    """Test 1: Admin can login and get token"""
    print("\n=== Test 1: Admin Authentication ===")

    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"username": "admin", "password": "TestSecure123!"}
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print_test("Admin login successful", True, f"Token: {token[:20]}...")
        return token
    else:
        print_test("Admin login failed", False, f"Status: {response.status_code}")
        return None

def test_create_api_key(admin_token):
    """Test 2: Create API key for testing"""
    print("\n=== Test 2: Create API Key ===")

    response = requests.post(
        f"{BASE_URL}/api/admin/api-keys",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        },
        json={"name": f"Test Key {datetime.now().strftime('%Y%m%d%H%M%S')}"}
    )

    if response.status_code == 200:
        data = response.json()
        api_key = data.get("key")
        print_test("API key created", True, f"Key: {api_key}")
        return api_key
    else:
        print_test("API key creation failed", False, f"Status: {response.status_code}")
        return None

def test_list_sessions_with_api_key(api_key):
    """Test 3: List sessions with API key (simulates instructor auth)"""
    print("\n=== Test 3: API Key Authentication ===")

    # Test with Authorization header (correct method)
    response = requests.get(
        f"{BASE_URL}/api/sessions/my-sessions",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code == 200:
        sessions = response.json()
        print_test("API key auth via header works", True, f"Found {len(sessions)} sessions")
        return True
    else:
        print_test("API key auth failed", False, f"Status: {response.status_code}, Body: {response.text}")
        return False

def test_create_session(api_key):
    """Test 4: Create a session with API key"""
    print("\n=== Test 4: Create Session ===")

    # Get CSRF token first
    csrf_response = requests.get(f"{BASE_URL}/api/csrf-token")
    if csrf_response.status_code != 200:
        print_test("Failed to get CSRF token", False)
        return None

    csrf_token = csrf_response.json()["csrf_token"]

    response = requests.post(
        f"{BASE_URL}/api/sessions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-CSRF-Token": csrf_token,
            "Content-Type": "application/json"
        },
        json={"title": f"Test Session {datetime.now().strftime('%H:%M:%S')}"}
    )

    if response.status_code == 200:
        session = response.json()
        print_test("Session created successfully", True,
                   f"Session Code: {session['session_code']}, Instructor Code: {session['instructor_code']}")
        return session
    else:
        print_test("Session creation failed", False, f"Status: {response.status_code}, Body: {response.text}")
        return None

def test_get_session_by_instructor_code(api_key, instructor_code):
    """Test 5: Get session details by instructor code"""
    print("\n=== Test 5: Get Session by Instructor Code ===")

    response = requests.get(
        f"{BASE_URL}/api/instructor/sessions/{instructor_code}",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code == 200:
        session = response.json()
        print_test("Session retrieved successfully", True, f"Title: {session['title']}")
        return True
    else:
        print_test("Session retrieval failed", False, f"Status: {response.status_code}")
        return False

def test_api_key_without_auth():
    """Test 6: Verify API key is required (should fail with 401)"""
    print("\n=== Test 6: Verify Authentication Required ===")

    response = requests.get(f"{BASE_URL}/api/sessions/my-sessions")

    if response.status_code == 401:
        print_test("Correctly rejects requests without API key", True, "Got 401 as expected")
        return True
    else:
        print_test("Should reject unauthenticated requests", False, f"Got {response.status_code} instead of 401")
        return False

def main():
    print("=" * 60)
    print("Phase 1 Testing: API Key Authentication Flow")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")

    # Check if server is running
    try:
        health = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if health.status_code == 200:
            print("✓ Server is running")
        else:
            print("✗ Server returned unexpected status")
            return
    except requests.exceptions.RequestException:
        print("✗ Server is not running at", BASE_URL)
        print("  Start the server with: ./venv/bin/python -m uvicorn main:app --reload")
        return

    # Run tests
    admin_token = test_admin_login()
    if not admin_token:
        print("\n✗ Cannot proceed without admin token")
        return

    api_key = test_create_api_key(admin_token)
    if not api_key:
        print("\n✗ Cannot proceed without API key")
        return

    # Core tests
    test_list_sessions_with_api_key(api_key)
    session = test_create_session(api_key)

    if session:
        test_get_session_by_instructor_code(api_key, session["instructor_code"])

    test_api_key_without_auth()

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nMANUAL TESTING INSTRUCTIONS:")
    print("-" * 60)
    print("1. Open browser to: http://localhost:8000")
    print("2. Clear all browser storage:")
    print("   - Open DevTools (F12)")
    print("   - Go to Application tab")
    print("   - Clear localStorage AND sessionStorage")
    print("3. Go to: http://localhost:8000/instructor-login")
    print(f"4. Enter this API key: {api_key}")
    print("5. Click 'View My Sessions'")
    print("6. ✓ EXPECTED: You should see sessions WITHOUT being prompted again")
    print("7. Navigate to: http://localhost:8000/instructor?code=" + (session["instructor_code"] if session else "XXX"))
    print("8. ✓ EXPECTED: Page loads WITHOUT prompting for API key")
    print("9. Refresh the page (F5)")
    print("10. ✓ EXPECTED: Still works WITHOUT prompting for API key")
    print("11. Close tab and open new tab to same URL")
    print("12. ✓ EXPECTED: NOW it should prompt for API key (session expired)")
    print("-" * 60)

if __name__ == "__main__":
    main()
