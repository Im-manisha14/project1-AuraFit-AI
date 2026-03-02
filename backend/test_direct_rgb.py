#!/usr/bin/env python3
"""
Test direct RGB classification (bypass method)
"""
import sys
sys.path.append('.')

from ml_models.hand_skin_detector import HandSkinToneDetector

def test_direct_rgb():
    print("=== Testing Direct RGB Classification ===")
    
    detector = HandSkinToneDetector()
    
    # Test different RGB values
    test_colors = [
        {"name": "Fair", "rgb": [240, 220, 190]},
        {"name": "Light", "rgb": [210, 180, 150]},
        {"name": "Medium", "rgb": [180, 150, 120]},
        {"name": "Olive", "rgb": [160, 130, 100]},
        {"name": "Deep", "rgb": [120, 90, 70]}
    ]
    
    for color_test in test_colors:
        print(f"\nTesting {color_test['name']} - RGB: {color_test['rgb']}")
        
        result = detector.detect_from_rgb(color_test['rgb'])
        
        if result.get('success'):
            print(f"✓ Detected as: {result.get('skin_tone')}")
            print(f"  Brightness: {result.get('brightness')}")
            print(f"  Recommended: {', '.join(result.get('recommended_colors', []))}")
        else:
            print(f"✗ Failed: {result.get('error')}")

if __name__ == "__main__":
    test_direct_rgb()