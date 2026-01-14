"""
Setup script to create test data for load testing.
Creates an instructor account, a class, and a meeting.

Usage:
  python setup_load_test.py
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.production")

BASE_URL = "http://localhost:8000"  # Always use localhost for load testing
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

print(f"\n{'='*70}")
print(f"🚀 RaiseMyHand Load Test Setup")
print(f"{'='*70}")
print(f"Target: {BASE_URL}")
print(f"Admin: {ADMIN_USERNAME}")
print()

# Step 1: Admin Login
print("📝 Step 1: Admin Login...")
try:
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        admin_token = response.json()["access_token"]
        print(f"✅ Admin logged in successfully")
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error logging in: {e}")
    exit(1)

headers = {"Authorization": f"Bearer {admin_token}"}

# Step 2: Create Instructor
print("\n📝 Step 2: Creating test instructor...")
instructor_data = {
    "username": "testinstructor",
    "email": "testinstructor@example.com",
    "password": "TestPassword123!",
    "display_name": "Test Instructor"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/instructors/register",
        json=instructor_data
    )
    if response.status_code == 200 or response.status_code == 201:
        instructor = response.json()
        instructor_id = instructor.get("id")
        print(f"✅ Instructor created: {instructor_data['username']} (ID: {instructor_id})")
        # Now login to get access token
        response = requests.post(
            f"{BASE_URL}/api/instructors/login",
            json={"username": instructor_data["username"], "password": instructor_data["password"]}
        )
        if response.status_code == 200:
            instructor_token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {instructor_token}"}
            print(f"✅ Instructor logged in successfully")
    else:
        # Try to login if instructor already exists
        print(f"⚠️  Instructor creation returned {response.status_code}, attempting login...")
        response = requests.post(
            f"{BASE_URL}/api/instructors/login",
            json={"username": instructor_data["username"], "password": instructor_data["password"]}
        )
        if response.status_code == 200:
            instructor_token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {instructor_token}"}
            # Get instructor ID from profile
            profile = requests.get(f"{BASE_URL}/api/instructors/profile", headers=headers)
            instructor_id = profile.json()["id"]
            print(f"✅ Using existing instructor (ID: {instructor_id})")
        else:
            print(f"❌ Instructor login failed: {response.status_code}")
            exit(1)
except Exception as e:
    print(f"❌ Error creating instructor: {e}")
    exit(1)

# Step 3: Create Class
print("\n📝 Step 3: Creating test class...")
class_data = {
    "name": "Load Test Class",
    "description": "A class for testing system scalability with 75-200 concurrent students"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/classes",
        json=class_data,
        headers=headers
    )
    if response.status_code == 201:
        class_info = response.json()
        class_id = class_info["id"]
        print(f"✅ Class created: '{class_data['name']}' (ID: {class_id})")
    else:
        print(f"❌ Class creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error creating class: {e}")
    exit(1)

# Step 4: Create Meeting
print("\n📝 Step 4: Creating test meeting...")
meeting_data = {
    "title": "Load Test Meeting - 200 Students",
    "password": "loadtest123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/classes/{class_id}/meetings",
        json=meeting_data,
        headers=headers
    )
    if response.status_code == 201:
        meeting = response.json()
        meeting_code = meeting.get("meeting_code", "unknown")
        meeting_password = meeting_data.get("password", "loadtest123")
        print(f"✅ Meeting created: '{meeting_data['title']}'")
        print(f"   Meeting Code: {meeting_code}")
        print(f"   Password: {meeting_password}")
    else:
        print(f"❌ Meeting creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error creating meeting: {e}")
    exit(1)

# Summary
print("\n" + "="*70)
print("✅ Setup Complete!")
print("="*70)
print(f"\nTest Data Created:")
print(f"  • Instructor Username: {instructor_data['username']}")
print(f"  • Instructor Email: {instructor_data['email']}")
print(f"  • Instructor Password: {instructor_data['password']}")
print(f"  • Class: Load Test Class")
print(f"  • Meeting Code: {meeting_code}")
print(f"  • Meeting Password: {meeting_password}")

print(f"\n🧪 Update tests/load/locustfile.py with:")
print(f'   MEETING_CODE = "{meeting_code}"')
print(f'   MEETING_PASSWORD = "{meeting_password}"')

print(f"\n🚀 Next Steps:")
print(f"1. Update tests/load/locustfile.py with the meeting code above")
print(f"2. Install dependencies: pip install -r tests/load/requirements.txt")
print(f"3. Run: locust -f tests/load/locustfile.py")
print(f"4. Open: http://localhost:8089")
print(f"5. Set users to 75-200 and spawn rate to 5-10")
print(f"\n{'='*70}\n")
