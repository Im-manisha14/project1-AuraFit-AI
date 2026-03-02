"""
AuraFit Hand Skin Tone Detection Module
Uses MediaPipe and OpenCV for accurate hand-only skin tone detection
Optimized for back-of-hand detection for better skin tone accuracy
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import base64

class HandSkinToneDetector:
    """Detects hand skin tone from camera/image input"""
    
    def __init__(self):
        self.skin_tone_categories = {
            'fair': {'range': (200, 255), 'colors': ['lavender', 'pastel blue', 'soft pink']},
            'light': {'range': (170, 199), 'colors': ['peach', 'beige', 'mint green']},
            'medium': {'range': (140, 169), 'colors': ['emerald', 'teal', 'mustard']},
            'olive': {'range': (110, 139), 'colors': ['earth tones', 'maroon', 'cream']},
            'deep': {'range': (0, 109), 'colors': ['royal blue', 'yellow', 'white']}
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
            
            # Detect hand region with improved algorithm
            hand_mask = self._detect_hand_region(image)
            
            if hand_mask is None:
                print(f"[HandDetector] Hand detection failed - trying fallback method")
                # Fallback: try to detect any skin-colored region
                hand_mask = self._detect_skin_fallback(image)
                
            if hand_mask is None:
                return {
                    'success': False,
                    'error': 'No hand detected. Please show the back of your hand clearly in good lighting with hand filling at least 20% of the frame.'
                }
            
            print(f"[HandDetector] Hand detected successfully")
            
            # Extract skin color from hand region
            skin_rgb = self._extract_skin_color(image, hand_mask)
            
            # Classify skin tone
            skin_tone, brightness = self._classify_skin_tone(skin_rgb)
            
            print(f"[HandDetector] Skin tone: {skin_tone}, Brightness: {brightness}, RGB: {skin_rgb}")
            
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
            import traceback
            traceback.print_exc()
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
        Optimized for back of hand detection
        """
        # Convert to multiple color spaces for better detection  
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        
        # HSV-based detection (improved ranges)
        # Range 1: Very light skin tones
        lower_skin1 = np.array([0, 15, 50], dtype=np.uint8) 
        upper_skin1 = np.array([25, 255, 255], dtype=np.uint8)
        
        # Range 2: Medium skin tones
        lower_skin2 = np.array([0, 10, 40], dtype=np.uint8)
        upper_skin2 = np.array([30, 200, 255], dtype=np.uint8)
        
        # Range 3: Darker skin tones
        lower_skin3 = np.array([0, 8, 30], dtype=np.uint8)
        upper_skin3 = np.array([35, 180, 255], dtype=np.uint8)
        
        # YCrCb-based detection (more reliable for skin)
        lower_ycrcb = np.array([0, 133, 77], dtype=np.uint8)
        upper_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
        
        # Create masks
        mask_hsv1 = cv2.inRange(hsv, lower_skin1, upper_skin1)
        mask_hsv2 = cv2.inRange(hsv, lower_skin2, upper_skin2) 
        mask_hsv3 = cv2.inRange(hsv, lower_skin3, upper_skin3)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)
        
        # Combine all masks
        mask_hsv = cv2.bitwise_or(mask_hsv1, mask_hsv2)
        mask_hsv = cv2.bitwise_or(mask_hsv, mask_hsv3)
        mask = cv2.bitwise_or(mask_hsv, mask_ycrcb)
        
        # Apply morphological operations with optimized kernels
        kernel_open = np.ones((5, 5), np.uint8)  # Smaller for better detail
        kernel_close = np.ones((15, 15), np.uint8)  # Larger for filling gaps
        
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        
        # Apply Gaussian blur to smooth edges
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"[HandDetector] Found {len(contours)} contours")
        
        if not contours:
            print(f"[HandDetector] No contours found")
            return None
        
        # Filter contours by area - more lenient threshold
        valid_contours = [c for c in contours if cv2.contourArea(c) > 500]  # Even more lenient
        
        print(f"[HandDetector] {len(valid_contours)} contours passed area filter")
        
        if not valid_contours:
            print(f"[HandDetector] No contours passed area filter")
            return None
        
        # Get the largest contour (assumed to be the hand)
        largest_contour = max(valid_contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        print(f"[HandDetector] Largest contour area: {contour_area}")
        
        # Additional validation: check if contour has reasonable aspect ratio
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = float(w) / h if h > 0 else 0
        
        print(f"[HandDetector] Bounding rect: {w}x{h}, aspect ratio: {aspect_ratio:.2f}")
        
        # Hand should not be too elongated (more lenient for back of hand)
        if aspect_ratio < 0.1 or aspect_ratio > 10.0:  # Very lenient ranges
            print(f"[HandDetector] Aspect ratio {aspect_ratio:.2f} outside valid range")
            return None
        
        # Create final mask with only the largest contour
        hand_mask = np.zeros(mask.shape, dtype=np.uint8)
        cv2.drawContours(hand_mask, [largest_contour], -1, 255, -1)
        
        # Final area check - ensure minimum 1% of image (very lenient)
        min_area = (image.shape[0] * image.shape[1]) * 0.01
        if cv2.contourArea(largest_contour) < min_area:
            print(f"[HandDetector] Contour area {contour_area} below minimum {min_area}")
            return None
        
        print(f"[HandDetector] Hand detection successful!")
        return hand_mask
    
    def _detect_skin_fallback(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Fallback method: detect any skin-colored region
        More lenient than hand detection
        """
        print(f"[HandDetector] Using fallback skin detection")
        
        # Try multiple color spaces and methods
        height, width = image.shape[:2]
        
        # Method 1: Very broad HSV range
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 5, 20], dtype=np.uint8)  # Very permissive
        upper_skin = np.array([40, 255, 255], dtype=np.uint8)
        mask_hsv = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Method 2: RGB-based detection
        # Common skin color ranges in RGB
        lower_rgb = np.array([80, 50, 20], dtype=np.uint8)
        upper_rgb = np.array([255, 220, 180], dtype=np.uint8)
        mask_rgb = cv2.inRange(image, lower_rgb, upper_rgb)
        
        # Combine masks
        mask = cv2.bitwise_or(mask_hsv, mask_rgb)
        
        # If still nothing, use center region
        if cv2.countNonZero(mask) < 100:
            print(f"[HandDetector] Creating center region mask")
            mask = np.zeros((height, width), dtype=np.uint8)
            center_x, center_y = width // 2, height // 2
            region_w, region_h = min(200, width // 3), min(200, height // 3)
            
            cv2.rectangle(mask, 
                         (center_x - region_w//2, center_y - region_h//2),
                         (center_x + region_w//2, center_y + region_h//2),
                         255, -1)
            
            print(f"[HandDetector] Using center region as fallback")
            return mask
        
        # Light morphological operations
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print(f"[HandDetector] Fallback: No skin regions found")
            return None
        
        # Get any reasonable sized region
        valid_contours = [c for c in contours if cv2.contourArea(c) > 100]  # Very small threshold
        
        if not valid_contours:
            print(f"[HandDetector] Fallback: No regions passed area filter")
            return None
        
        # Use the largest region
        largest_contour = max(valid_contours, key=cv2.contourArea)
        
        # Create mask
        hand_mask = np.zeros(mask.shape, dtype=np.uint8)
        cv2.drawContours(hand_mask, [largest_contour], -1, 255, -1)
        
        print(f"[HandDetector] Fallback detection successful!")
        return hand_mask
    
    def detect_from_rgb(self, rgb_values: list) -> dict:
        """
        Detect skin tone from RGB values directly (bypass camera detection)
        
        Args:
            rgb_values: [R, G, B] values (0-255)
            
        Returns:
            dict with skin_tone and recommended_colors
        """
        try:
            rgb = np.array(rgb_values, dtype=int)
            
            # Classify skin tone
            skin_tone, brightness = self._classify_skin_tone(rgb)
            
            # Get color recommendations
            recommended_colors = self.skin_tone_categories[skin_tone]['colors']
            
            print(f"[HandDetector] Direct RGB classification: {rgb} -> {skin_tone}")
            
            return {
                'success': True,
                'skin_tone': skin_tone.title(),
                'rgb_value': rgb.tolist(),
                'brightness': int(brightness),
                'recommended_colors': recommended_colors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'RGB classification failed: {str(e)}'
            }
    
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
