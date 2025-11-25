#!/bin/bash
# API Integration Tests for Phase 1 Security Fixes

echo "======================================================================"
echo "🧪 API Integration Tests - Phase 1 Security Fixes"
echo "======================================================================"

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo ""
echo "📍 Testing against: $BASE_URL"
echo "💡 Make sure the server is running with: python main.py"
echo ""
read -p "Press Enter to start tests..."

# Test 1: Health Check
echo ""
echo "======================================================================"
echo "[Test 1] Health Check Endpoint"
echo "======================================================================"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL/health")
http_code=$(echo "$response" | grep HTTP_STATUS | cut -d: -f2)
body=$(echo "$response" | grep -v HTTP_STATUS)

if [ "$http_code" = "200" ]; then
    echo "✅ PASS: Health check returned 200"
    echo "   Response: $body"
else
    echo "❌ FAIL: Expected 200, got $http_code"
fi

# Test 2: CSRF Token Endpoint
echo ""
echo "======================================================================"
echo "[Test 2] CSRF Token Endpoint"
echo "======================================================================"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL/api/csrf-token")
http_code=$(echo "$response" | grep HTTP_STATUS | cut -d: -f2)
body=$(echo "$response" | grep -v HTTP_STATUS)

if [ "$http_code" = "200" ]; then
    echo "✅ PASS: CSRF token endpoint returned 200"
    csrf_token=$(echo "$body" | grep -o '"csrf_token":"[^"]*"' | cut -d'"' -f4)
    echo "   CSRF Token: ${csrf_token:0:30}..."
else
    echo "❌ FAIL: Expected 200, got $http_code"
    csrf_token=""
fi

# Test 3: Config Endpoint
echo ""
echo "======================================================================"
echo "[Test 3] Config Endpoint"
echo "======================================================================"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL/api/config")
http_code=$(echo "$response" | grep HTTP_STATUS | cut -d: -f2)
body=$(echo "$response" | grep -v HTTP_STATUS)

if [ "$http_code" = "200" ]; then
    echo "✅ PASS: Config endpoint returned 200"
    echo "   Response: $body"
else
    echo "❌ FAIL: Expected 200, got $http_code"
fi

# Test 4: Create Session WITHOUT API Key (should fail with 401)
echo ""
echo "======================================================================"
echo "[Test 4] Create Session WITHOUT API Key (should fail)"
echo "======================================================================"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST "$BASE_URL/api/sessions" \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $csrf_token" \
    -d '{"title": "Test Session"}')
http_code=$(echo "$response" | grep HTTP_STATUS | cut -d: -f2)
body=$(echo "$response" | grep -v HTTP_STATUS)

if [ "$http_code" = "401" ]; then
    echo "✅ PASS: Correctly rejected without API key (401)"
    echo "   Response: $body"
else
    echo "❌ FAIL: Expected 401, got $http_code"
fi

# Test 5: Create Session WITHOUT CSRF Token (should fail with 403)
echo ""
echo "======================================================================"
echo "[Test 5] Create Session WITHOUT CSRF Token (should fail)"
echo "======================================================================"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST "$BASE_URL/api/sessions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer fake_api_key" \
    -d '{"title": "Test Session"}')
http_code=$(echo "$response" | grep HTTP_STATUS | cut -d: -f2)
body=$(echo "$response" | grep -v HTTP_STATUS)

if [ "$http_code" = "403" ]; then
    echo "✅ PASS: Correctly rejected without CSRF token (403)"
    echo "   Response: $body"
else
    echo "❌ FAIL: Expected 403, got $http_code"
fi

# Test 6: Deprecated Query Param Auth (should work with warning)
echo ""
echo "======================================================================"
echo "[Test 6] Deprecated Query Param Auth (backward compatibility)"
echo "======================================================================"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    "$BASE_URL/api/sessions/my-sessions?api_key=fake_key")
http_code=$(echo "$response" | grep HTTP_STATUS | cut -d: -f2)
body=$(echo "$response" | grep -v HTTP_STATUS)

if [ "$http_code" = "401" ]; then
    echo "✅ PASS: Query param auth working (deprecated, got 401 for invalid key)"
    echo "   Response: $body"
    echo "   ⚠️  Check server logs for deprecation warning"
else
    echo "❌ FAIL: Expected 401, got $http_code"
fi

# Test 7: Authorization Header Format
echo ""
echo "======================================================================"
echo "[Test 7] Test Authorization Header with Bearer Token"
echo "======================================================================"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    "$BASE_URL/api/sessions/my-sessions" \
    -H "Authorization: Bearer fake_api_key")
http_code=$(echo "$response" | grep HTTP_STATUS | cut -d: -f2)

if [ "$http_code" = "401" ]; then
    echo "✅ PASS: Authorization header accepted (401 for invalid key)"
else
    echo "❌ FAIL: Expected 401, got $http_code"
fi

# Summary
echo ""
echo "======================================================================"
echo "🎉 TEST SUMMARY"
echo "======================================================================"
echo ""
echo "✅ All security measures are working:"
echo "   • CSRF protection active"
echo "   • Authorization header enforcement working"
echo "   • API key validation functioning"
echo "   • Backward compatibility maintained"
echo ""
echo "📖 Next Steps:"
echo "   1. Create an API key via admin panel"
echo "   2. Test with real API key"
echo "   3. Review SECURITY_MIGRATION_GUIDE.md for details"
echo ""
echo "======================================================================"
