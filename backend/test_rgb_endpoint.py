#!/usr/bin/env python3
"""
Test manual RGB detection endpoint
"""
import requests
import json

def test_rgb_endpoint():
    print("=== Testing Manual RGB Detection Endpoint ===")
    
    # Test different skin tone RGB values
    test_colors = [
        {"name": "Fair", "rgb": [240, 220, 190]},
        {"name": "Light", "rgb": [210, 180, 150]},
        {"name": "Medium", "rgb": [180, 150, 120]},
        {"name": "Olive", "rgb": [160, 130, 100]},
        {"name": "Deep", "rgb": [120, 90, 70]}
    ]
    
    url = "http://localhost:5000/api/ai/detect-skin-tone"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMDU3MTc4NywianRpIjoiNjc5MDg5NzMtNGIzZi00NjMzLWFjOTItYzYwN2Y5ZGRmNGFkIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjMiLCJuYmYiOjE3MzA1NzE3ODcsImV4cCI6MTczMDU3NTM4N30.6rDejxrr7ZVdOoctwf9vjUs_lHWOwdULNIh7KO1_8Qo",  # Sample token
        "Content-Type": "application/json"
    }
    
    for color_test in test_colors:
        try:
            data = {"rgb": color_test["rgb"]}
            print(f"\nTesting {color_test['name']} skin - RGB: {color_test['rgb']}")
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Success! Detected as: {result.get('skin_tone')}")
                print(f"  Brightness: {result.get('brightness')}")
                print(f"  Recommended: {', '.join(result.get('recommended_colors', []))}")
            else:
                print(f"✗ Failed: {response.status_code}")
                if response.text:
                    print(f"  Error: {response.text}")
                    
        except Exception as e:
            print(f"✗ Exception: {e}")

if __name__ == "__main__":
    test_rgb_endpoint()