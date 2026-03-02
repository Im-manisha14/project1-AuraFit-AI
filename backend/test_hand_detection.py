#!/usr/bin/env python3
"""
Test script for hand skin tone detection
"""
import sys
sys.path.append('.')

from ml_models.hand_skin_detector import HandSkinToneDetector
import base64
import cv2
import numpy as np

def test_detection():
    print("=== Hand Skin Tone Detection Test ===")
    
    # Initialize detector
    try:
        detector = HandSkinToneDetector()
        print("✓ Detector initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize detector: {e}")
        return
    
    # Test with a simple synthetic image (skin-colored rectangle)
    try:
        # Create a simple skin-colored image (beige/peach color)
        width, height = 640, 480
        skin_color_bgr = [120, 150, 180]  # BGR skin-like color (OpenCV uses BGR)
        
        # Create image
        image = np.full((height, width, 3), skin_color_bgr, dtype=np.uint8)
        
        # Add some variation to make it more realistic
        center_x, center_y = width // 2, height // 2
        hand_width, hand_height = 200, 300
        
        # Create a hand-like rectangular region with slight color variation
        for y in range(center_y - hand_height//2, center_y + hand_height//2):
            for x in range(center_x - hand_width//2, center_x + hand_width//2):
                if 0 <= y < height and 0 <= x < width:
                    # Add slight variation
                    variation = np.random.randint(-10, 10, 3)
                    color = np.clip(np.array(skin_color_bgr) + variation, 0, 255)
                    image[y, x] = color
        
        # Convert to base64 (simulate frontend capture)
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{image_base64}"
        
        print("✓ Created test image")
        print(f"  Image size: {width}x{height}")
        print(f"  Test color BGR: {skin_color_bgr}")
        
        # Test detection
        result = detector.detect_skin_from_image(image_data_url)
        
        print("\n=== Detection Result ===")
        if result.get('success'):
            print("✓ Detection successful!")
            print(f"  Skin Tone: {result.get('skin_tone')}")
            print(f"  RGB Value: {result.get('rgb_value')}")
            print(f"  Brightness: {result.get('brightness')}")
            print(f"  Recommended Colors: {result.get('recommended_colors')}")
        else:
            print("✗ Detection failed!")
            print(f"  Error: {result.get('error')}")
            
        # Test with manual color classification (bypass detection)
        print("\n=== Manual Color Classification Test ===")
        rgb_color = np.array([180, 150, 120])  # RGB
        tone, brightness = detector._classify_skin_tone(rgb_color)
        print(f"  Manual RGB: {rgb_color}")
        print(f"  Classified as: {tone.title()}")
        print(f"  Brightness: {brightness}")
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detection()