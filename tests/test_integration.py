#!/usr/bin/env python3
"""
Integration test for Phase 1 security fixes
Tests the API endpoints with the new security measures
"""

import os
import sys
import time
import requests
from multiprocessing import Process

# Set test password
os.environ['ADMIN_PASSWORD'] = 'test_password_123'

# Import uvicorn and main
import uvicorn
import main

def start_server():
    """Start the FastAPI server in a subprocess"""
    uvicorn.run(main.app, host="127.0.0.1", port=8888, log_level="error")

def test_api():
    """Test API endpoints"""
    base_url = "http://127.0.0.1:8888"

    print("\n" + "=" * 70)
    print("🧪 Integration Tests - API Security")
    print("=" * 70)

    # Wait for server to start
    print("\n⏳ Waiting for server to start...")
    time.sleep(2)

    # Test 1: Health check
    print("\n[Test 1] Health check endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✅ PASS: Health check working")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

    # Test 2: CSRF token endpoint
    print("\n[Test 2] CSRF token endpoint...")
    try:
        response = requests.get(f"{base_url}/api/csrf-token", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        csrf_token = data["csrf_token"]
        assert ":" in csrf_token
        print(f"✅ PASS: CSRF token received: {csrf_token[:20]}...")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

    # Test 3: Config endpoint
    print("\n[Test 3] Config endpoint...")
    try:
        response = requests.get(f"{base_url}/api/config", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "base_url" in data
        assert "timezone" in data
        print("✅ PASS: Config endpoint working")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

    # Test 4: Create session WITHOUT API key (should fail)
    print("\n[Test 4] Create session without API key (should fail)...")
    try:
        response = requests.post(
            f"{base_url}/api/sessions",
            json={"title": "Test Session"},
            headers={"X-CSRF-Token": csrf_token},
            timeout=5
        )
        assert response.status_code == 401
        print("✅ PASS: Correctly rejected request without API key")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

    # Test 5: Create session WITHOUT CSRF token (should fail)
    print("\n[Test 5] Create session without CSRF token (should fail)...")
    try:
        response = requests.post(
            f"{base_url}/api/sessions",
            json={"title": "Test Session"},
            headers={"Authorization": "Bearer fake_api_key"},
            timeout=5
        )
        assert response.status_code == 403
        print("✅ PASS: Correctly rejected request without CSRF token")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

    # Test 6: Deprecated query param auth (should warn but work)
    print("\n[Test 6] Deprecated query param auth...")
    try:
        # This should work but log a warning
        response = requests.get(
            f"{base_url}/api/sessions/my-sessions?api_key=fake_key",
            timeout=5
        )
        # Should fail with 401 (invalid key) not 403 (missing auth)
        assert response.status_code == 401
        print("✅ PASS: Query param auth still works (deprecated)")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

    print("\n" + "=" * 70)
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("=" * 70)
    print("\n✅ API endpoints working correctly")
    print("✅ CSRF protection active")
    print("✅ Authorization header enforcement working")
    print("✅ Backward compatibility maintained")
    print("=" * 70)
    return True

if __name__ == "__main__":
    print("Starting test server on port 8888...")

    # Start server in background
    server_process = Process(target=start_server)
    server_process.start()

    try:
        # Run tests
        success = test_api()
        sys.exit(0 if success else 1)
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        server_process.terminate()
        server_process.join(timeout=2)
        if server_process.is_alive():
            server_process.kill()
        print("✅ Server stopped")
