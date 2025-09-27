#!/usr/bin/env python3
"""
Test script to verify backend API integration.
This script tests the REST endpoints that the frontend will use.
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8009"
TEST_USER = "testuser"
TEST_PASSWORD = "testpass"

def test_health_check() -> bool:
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False

def test_user_registration() -> bool:
    """Test user registration."""
    print("🔍 Testing user registration...")
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json={"username": TEST_USER, "password": TEST_PASSWORD},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User registration successful: {data}")
            return True
        elif response.status_code == 400:
            # User might already exist
            data = response.json()
            if "already exists" in data.get("detail", ""):
                print(f"✅ User already exists (expected): {data}")
                return True
            else:
                print(f"❌ Registration failed: {data}")
                return False
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration error: {e}")
        return False

def test_user_login() -> str | None:
    """Test user login and return token."""
    print("🔍 Testing user login...")
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful: {data}")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Login error: {e}")
        return None

def test_session_stats(token: str) -> bool:
    """Test session statistics endpoint."""
    print("🔍 Testing session stats...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/sessions/stats", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session stats retrieved: {data}")
            return True
        else:
            print(f"❌ Session stats failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Session stats error: {e}")
        return False

def test_user_sessions(token: str) -> bool:
    """Test user sessions endpoint."""
    print("🔍 Testing user sessions...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/sessions/my", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User sessions retrieved: {data}")
            return True
        else:
            print(f"❌ User sessions failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ User sessions error: {e}")
        return False

def test_user_info(token: str) -> bool:
    """Test user info endpoint."""
    print("🔍 Testing user info...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/me", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User info retrieved: {data}")
            return True
        else:
            print(f"❌ User info failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ User info error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting backend API integration tests...")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("❌ Health check failed - backend might not be running")
        sys.exit(1)
    
    # Test user registration
    if not test_user_registration():
        print("❌ User registration failed")
        sys.exit(1)
    
    # Test user login
    token = test_user_login()
    if not token:
        print("❌ User login failed")
        sys.exit(1)
    
    # Test authenticated endpoints
    if not test_user_info(token):
        print("❌ User info test failed")
        sys.exit(1)
    
    if not test_session_stats(token):
        print("❌ Session stats test failed")
        sys.exit(1)
    
    if not test_user_sessions(token):
        print("❌ User sessions test failed")
        sys.exit(1)
    
    print("=" * 50)
    print("✅ All tests passed! Backend API is ready for frontend integration.")
    print(f"🔑 Test token: {token[:20]}...")
    print("📝 You can use this token to test the frontend integration.")

if __name__ == "__main__":
    main()
