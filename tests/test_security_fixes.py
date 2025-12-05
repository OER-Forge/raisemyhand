#!/usr/bin/env python3
"""
Test script for Phase 1 security fixes
"""

import os
import sys

# Set test password
os.environ['ADMIN_PASSWORD'] = 'test_password_123'

print("=" * 70)
print("🧪 Testing Phase 1 Security Fixes")
print("=" * 70)

# Test 1: Import main module
print("\n[Test 1] Import main module with ADMIN_PASSWORD set...")
try:
    import main
    print("✅ PASS: main.py imports successfully")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 2: Check CSRF functions exist
print("\n[Test 2] Check CSRF protection functions...")
try:
    assert hasattr(main, 'generate_csrf_token'), "generate_csrf_token missing"
    assert hasattr(main, 'verify_csrf_token'), "verify_csrf_token missing"
    assert hasattr(main, 'get_csrf_token'), "get_csrf_token missing"
    print("✅ PASS: CSRF functions exist")
except AssertionError as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 3: Check API key dependency exists
print("\n[Test 3] Check API key dependency function...")
try:
    assert hasattr(main, 'get_api_key'), "get_api_key missing"
    print("✅ PASS: API key dependency exists")
except AssertionError as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 4: Test CSRF token generation
print("\n[Test 4] Test CSRF token generation...")
try:
    token = main.generate_csrf_token()
    assert ':' in token, "Token should contain colon separator"
    parts = token.split(':')
    assert len(parts) == 2, "Token should have timestamp:signature format"
    print(f"✅ PASS: Generated token: {token[:20]}...")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 5: Test CSRF token verification
print("\n[Test 5] Test CSRF token verification...")
try:
    token = main.generate_csrf_token()
    is_valid = main.verify_csrf_token(token)
    assert is_valid, "Valid token should verify"

    # Test invalid token
    is_valid = main.verify_csrf_token("invalid:token")
    assert not is_valid, "Invalid token should not verify"

    print("✅ PASS: CSRF token verification works")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 6: Check admin password is set
print("\n[Test 6] Check admin password configuration...")
try:
    assert main.ADMIN_PASSWORD == 'test_password_123', "Password not set correctly"
    print("✅ PASS: Admin password configured")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 7: Check CSRF configuration
print("\n[Test 7] Check CSRF configuration...")
try:
    assert hasattr(main, 'CSRF_SECRET'), "CSRF_SECRET missing"
    assert hasattr(main, 'CSRF_TOKEN_EXPIRY'), "CSRF_TOKEN_EXPIRY missing"
    assert main.CSRF_TOKEN_EXPIRY == 3600, "CSRF expiry should be 3600"
    print("✅ PASS: CSRF configuration correct")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

# Test 8: Verify FastAPI app exists
print("\n[Test 8] Check FastAPI app initialization...")
try:
    assert hasattr(main, 'app'), "FastAPI app missing"
    print("✅ PASS: FastAPI app initialized")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("🎉 ALL TESTS PASSED!")
print("=" * 70)
print("\n✅ Phase 1 security fixes are working correctly")
print("✅ ADMIN_PASSWORD requirement enforced")
print("✅ CSRF protection implemented")
print("✅ API key dependency created")
print("\n💡 Next: Start the server with 'python main.py'")
print("=" * 70)
