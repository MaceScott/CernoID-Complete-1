import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_register():
    """Test user registration endpoint."""
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = requests.post(url, json=data)
    print("\nRegistration Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

def test_login():
    """Test user login endpoint."""
    url = f"{BASE_URL}/auth/token"
    data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(url, data=data)
    print("\nLogin Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"\nAccess Token: {token}")
        return token
    return None

if __name__ == "__main__":
    print("Testing Authentication Endpoints...")
    test_register()
    test_login() 