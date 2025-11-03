#!/usr/bin/env python3
"""
Backend API Testing for Mountain Photography Theme
Tests the Contact Form Submission and Image Upload endpoints
"""

import requests
import json
import os
import io
from typing import Dict, Any

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    return "http://localhost:8001"

BACKEND_URL = get_backend_url()
API_BASE = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE}")

def test_contact_form_submission():
    """Test contact form submission endpoint"""
    print("\n=== Testing Contact Form Submission Endpoint ===")
    
    # Test 1: Valid contact form submission
    print("\n1. Testing valid contact form submission...")
    payload = {
        "name": "Andrei Popescu",
        "email": "andrei.popescu@example.com",
        "phone": "+40721234567",
        "message": "Sunt interesat de serviciile de fotografie montana. Ati putea sa imi trimiteti mai multe detalii despre pachetele disponibile?",
        "notification_email": "contact@mountainshots.ro"
    }
    
    try:
        response = requests.post(f"{API_BASE}/contact/submit", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            if (response_data.get("success") == True and 
                "Form submitted successfully" in response_data.get("message", "") and
                response_data.get("data", {}).get("name") == "Andrei Popescu" and
                response_data.get("data", {}).get("email") == "andrei.popescu@example.com"):
                print("✅ PASS: Contact form submitted successfully with correct response")
            else:
                print("❌ FAIL: Response format incorrect")
                print(f"Expected success=True, message='Form submitted successfully'")
                print(f"Got: {response_data}")
        else:
            print(f"❌ FAIL: Expected status 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Missing required fields
    print("\n2. Testing missing required name field...")
    payload = {
        "email": "test@example.com",
        "message": "Test message"
    }
    
    try:
        response = requests.post(f"{API_BASE}/contact/submit", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:  # Pydantic validation error
            print("✅ PASS: Correctly rejected request without required name field")
        else:
            print("❌ FAIL: Should have rejected request without name field")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Missing email field
    print("\n3. Testing missing required email field...")
    payload = {
        "name": "Test User",
        "message": "Test message"
    }
    
    try:
        response = requests.post(f"{API_BASE}/contact/submit", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ PASS: Correctly rejected request without required email field")
        else:
            print("❌ FAIL: Should have rejected request without email field")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: Missing message field
    print("\n4. Testing missing required message field...")
    payload = {
        "name": "Test User",
        "email": "test@example.com"
    }
    
    try:
        response = requests.post(f"{API_BASE}/contact/submit", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ PASS: Correctly rejected request without required message field")
        else:
            print("❌ FAIL: Should have rejected request without message field")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 5: Optional fields (phone and notification_email)
    print("\n5. Testing form submission without optional fields...")
    payload = {
        "name": "Maria Ionescu",
        "email": "maria.ionescu@gmail.com",
        "message": "Vreau sa rezerv o sedinta foto in muntii Carpati pentru luna viitoare."
    }
    
    try:
        response = requests.post(f"{API_BASE}/contact/submit", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            if (response_data.get("success") == True and 
                "Form submitted successfully" in response_data.get("message", "")):
                print("✅ PASS: Contact form works without optional fields")
            else:
                print("❌ FAIL: Response format incorrect for optional fields test")
        else:
            print(f"❌ FAIL: Expected status 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_image_upload_endpoint():
    """Test image upload endpoint functionality"""
    print("\n=== Testing Image Upload Endpoint ===")
    
    # Test 1: Valid image upload (simulate PNG file)
    print("\n1. Testing valid PNG image upload...")
    
    # Create a simple PNG-like file content (minimal PNG header)
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    files = {
        'file': ('mountain_landscape.png', io.BytesIO(png_content), 'image/png')
    }
    
    try:
        response = requests.post(f"{API_BASE}/upload/image", files=files, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            if (response_data.get("success") == True and 
                response_data.get("url", "").startswith("/api/uploads/") and
                response_data.get("filename", "").endswith(".png")):
                print("✅ PASS: PNG image uploaded successfully")
                print(f"✅ File URL: {response_data.get('url')}")
                print(f"✅ Filename: {response_data.get('filename')}")
            else:
                print("❌ FAIL: Response format incorrect for image upload")
                print(f"Expected success=True, url starting with '/api/uploads/', filename ending with '.png'")
                print(f"Got: {response_data}")
        else:
            print(f"❌ FAIL: Expected status 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Valid JPEG upload
    print("\n2. Testing valid JPEG image upload...")
    
    # Create a minimal JPEG file content
    jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    files = {
        'file': ('mountain_peak.jpg', io.BytesIO(jpeg_content), 'image/jpeg')
    }
    
    try:
        response = requests.post(f"{API_BASE}/upload/image", files=files, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            if (response_data.get("success") == True and 
                response_data.get("url", "").startswith("/api/uploads/") and
                response_data.get("filename", "").endswith(".jpg")):
                print("✅ PASS: JPEG image uploaded successfully")
            else:
                print("❌ FAIL: Response format incorrect for JPEG upload")
        else:
            print(f"❌ FAIL: Expected status 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Invalid file type
    print("\n3. Testing invalid file type upload...")
    
    files = {
        'file': ('document.txt', io.BytesIO(b'This is a text file'), 'text/plain')
    }
    
    try:
        response = requests.post(f"{API_BASE}/upload/image", files=files, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            response_data = response.json()
            if "Invalid file type" in response_data.get("detail", ""):
                print("✅ PASS: Correctly rejected invalid file type")
            else:
                print("❌ FAIL: Error message doesn't indicate invalid file type")
        else:
            print(f"❌ FAIL: Expected status 400, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: No file provided
    print("\n4. Testing upload without file...")
    
    try:
        response = requests.post(f"{API_BASE}/upload/image", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:  # FastAPI validation error
            print("✅ PASS: Correctly rejected request without file")
        else:
            print(f"❌ FAIL: Expected status 422, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 5: WebP format support
    print("\n5. Testing WebP image upload...")
    
    # Create a minimal WebP file content
    webp_content = b'RIFF\x1a\x00\x00\x00WEBPVP8 \x0e\x00\x00\x00\x90\x01\x00\x9d\x01*\x01\x00\x01\x00\x00\x00\x00'
    
    files = {
        'file': ('mountain_sunset.webp', io.BytesIO(webp_content), 'image/webp')
    }
    
    try:
        response = requests.post(f"{API_BASE}/upload/image", files=files, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            if (response_data.get("success") == True and 
                response_data.get("filename", "").endswith(".webp")):
                print("✅ PASS: WebP image uploaded successfully")
            else:
                print("❌ FAIL: Response format incorrect for WebP upload")
        else:
            print(f"❌ FAIL: Expected status 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_backend_health():
    """Test basic backend connectivity"""
    print("\n=== Testing Backend Health ===")
    
    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("message") == "Hello World":
                print("✅ PASS: Backend is accessible and responding correctly")
            else:
                print("❌ FAIL: Backend response format incorrect")
        else:
            print("❌ FAIL: Backend health check failed")
    except Exception as e:
        print(f"❌ ERROR: Cannot reach backend: {e}")

def main():
    """Run all Mountain Photography Theme API tests"""
    print("🚀 Starting Mountain Photography Theme API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    
    # Test backend connectivity first
    test_backend_health()
    
    # Test contact form submission endpoint
    test_contact_form_submission()
    
    # Test image upload endpoint
    test_image_upload_endpoint()
    
    print("\n🏁 Mountain Photography Theme API Tests Complete")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()