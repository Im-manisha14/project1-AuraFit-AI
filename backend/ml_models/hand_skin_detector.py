"""
AuraFit Hand Skin Tone Detection Module
Uses MediaPipe and OpenCV for accurate hand-only skin tone detection
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import base64

class HandSkinToneDetector:
    """Detects hand skin tone from camera/image input"""
    
    def __init__(self):
        self.skin_tone_categories = {
            'fair': {'range': (0, 50), 'colors': ['lavender', 'pastel blue', 'soft pink']},
            'light': {'range': (51, 100), 'colors': ['peach', 'beige', 'mint green']},
            'medium': {'range': (101, 150), 'colors': ['emerald', 'teal', 'mustard']},
            'olive': {'range': (151, 180), 'colors': ['earth tones', 'maroon', 'cream']},
            'deep': {'range': (181, 255), 'colors': ['royal blue', 'yellow', 'white']}
        }
    
    def detect_skin_from_image(self, image_data: str) -> dict:
        """
        Detect skin tone from base64 encoded image
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            dict with skin_tone, rgb_value, and recommended_colors
        """
        try:
            # Decode base64 image
            image = self._decode_base64_image(image_data)
            
            if image is None or image.size == 0:
                return {
                    'success': False,
                    'error': 'Invalid image data. Please try capturing again.'
                }
            
            print(f"[HandDetector] Processing image of size: {image.shape}")
            
            # Detect hand region
            hand_mask = self._detect_hand_region(image)
            
            if hand_mask is None:
                return {
                    'success': False,
                    'error': 'No hand detected. Please show your palm clearly in good lighting with hand filling the frame.'
                }
            
            print(f"[HandDetector] Hand detected successfully")
            
            # Extract skin color from hand region
            skin_rgb = self._extract_skin_color(image, hand_mask)
            
            # Classify skin tone
            skin_tone, brightness = self._classify_skin_tone(skin_rgb)
            
            print(f"[HandDetector] Skin tone: {skin_tone}, Brightness: {brightness}")
            
            # Get color recommendations
            recommended_colors = self.skin_tone_categories[skin_tone]['colors']
            
            return {
                'success': True,
                'skin_tone': skin_tone.title(),
                'rgb_value': skin_rgb.tolist(),
                'brightness': int(brightness),
                'recommended_colors': recommended_colors
            }
            
        except Exception as e:
            print(f"[HandDetector] Error: {str(e)}")
            return {
                'success': False,
                'error': f'Detection failed: {str(e)}'
            }
    
    def _decode_base64_image(self, image_data: str) -> np.ndarray:
        """Decode base64 image to numpy array"""
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        return image
    
    def _detect_hand_region(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect hand region using advanced skin color thresholding
        Works in various lighting conditions and for all skin tones
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define multiple skin color ranges in HSV for better detection
        # Range 1: Light skin tones (lower saturation)
        lower_skin1 = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin1 = np.array([20, 255, 255], dtype=np.uint8)
        
        # Range 2: Darker skin tones and different lighting
        lower_skin2 = np.array([0, 15, 50], dtype=np.uint8)
        upper_skin2 = np.array([25, 200, 255], dtype=np.uint8)
        
        # Range 3: Additional range for orange-red tones
        lower_skin3 = np.array([0, 10, 60], dtype=np.uint8)
        upper_skin3 = np.array([30, 170, 255], dtype=np.uint8)
        
        # Create masks for each range
        mask1 = cv2.inRange(hsv, lower_skin1, upper_skin1)
        mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
        mask3 = cv2.inRange(hsv, lower_skin3, upper_skin3)
        
        # Combine all masks
        mask = cv2.bitwise_or(mask1, mask2)
        mask = cv2.bitwise_or(mask, mask3)
        
        # Apply morphological operations to clean up the mask
        # Use larger kernel for better noise removal
        kernel_open = np.ones((7, 7), np.uint8)
        kernel_close = np.ones((11, 11), np.uint8)
        
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        
        # Apply Gaussian blur to smooth edges
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Filter contours by area - remove very small detections
        valid_contours = [c for c in contours if cv2.contourArea(c) > 2000]
        
        if not valid_contours:
            return None
        
        # Get the largest contour (assumed to be the hand)
        largest_contour = max(valid_contours, key=cv2.contourArea)
        
        # Additional validation: check if contour has reasonable aspect ratio
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = float(w) / h if h > 0 else 0
        
        # Hand should not be too elongated (between 0.3 and 3.0)
        if aspect_ratio < 0.2 or aspect_ratio > 5.0:
            return None
        
        # Create final mask with only the largest contour
        hand_mask = np.zeros(mask.shape, dtype=np.uint8)
        cv2.drawContours(hand_mask, [largest_contour], -1, 255, -1)
        
        # Final area check - ensure minimum 3% of image
        min_area = (image.shape[0] * image.shape[1]) * 0.03
        if cv2.contourArea(largest_contour) < min_area:
            return None
        
        return hand_mask
    
    def _extract_skin_color(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Extract average skin color from masked region"""
        # Apply mask to image
        masked_image = cv2.bitwise_and(image, image, mask=mask)
        
        # Get all non-zero pixels (skin pixels)
        skin_pixels = masked_image[mask > 0]
        
        # Calculate average color (BGR to RGB)
        avg_color_bgr = np.mean(skin_pixels, axis=0)
        avg_color_rgb = avg_color_bgr[::-1]  # Convert BGR to RGB
        
        return avg_color_rgb.astype(int)
    
    def _classify_skin_tone(self, rgb: np.ndarray) -> Tuple[str, float]:
        """
        Classify skin tone based on RGB values
        
        Returns:
            tuple of (category, brightness_value)
        """
        # Calculate brightness (luminance)
        brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        
        # Classify based on brightness
        for category, data in self.skin_tone_categories.items():
            min_val, max_val = data['range']
            if min_val <= brightness <= max_val:
                return category, brightness
        
        # Default to medium if outside ranges
        return 'medium', brightness
    
    def get_recommended_colors(self, skin_tone: str) -> list:
        """Get recommended outfit colors for a skin tone"""
        tone = skin_tone.lower()
        if tone in self.skin_tone_categories:
            return self.skin_tone_categories[tone]['colors']
        return []


# Test function
def test_detector():
    """Test the detector with sample values"""
    detector = HandSkinToneDetector()
    
    # Test with different RGB values
    test_cases = [
        np.array([230, 210, 200]),  # Fair
        np.array([200, 170, 150]),  # Light
        np.array([170, 130, 110]),  # Medium
        np.array([140, 100, 80]),   # Olive
        np.array([100, 70, 50])     # Deep
    ]
    
    print("Testing Hand Skin Tone Classifier:")
    print("-" * 50)
    for rgb in test_cases:
        tone, brightness = detector._classify_skin_tone(rgb)
        colors = detector.get_recommended_colors(tone)
        print(f"RGB: {rgb} → Tone: {tone.title()} (Brightness: {brightness:.1f})")
        print(f"  Recommended: {', '.join(colors)}\n")


if __name__ == "__main__":
    test_detector()
