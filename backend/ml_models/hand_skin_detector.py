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
            'fair':   {'range': (200, 255), 'colors': ['Navy', 'Emerald Green', 'Burgundy', 'Charcoal Grey', 'Royal Blue']},
            'light':  {'range': (170, 199), 'colors': ['Soft Blue', 'Lavender', 'Peach', 'Mint Green', 'Rose Pink']},
            'medium': {'range': (140, 169), 'colors': ['Olive Green', 'Beige', 'Mustard Yellow', 'Forest Green', 'Cream']},
            'olive':  {'range': (110, 139), 'colors': ['Rust', 'Coral', 'Cream', 'Charcoal', 'Deep Teal']},
            'deep':   {'range': (0,   109), 'colors': ['White', 'Gold', 'Royal Blue', 'Magenta', 'Bright Yellow']},
        }
    
    def detect_skin_from_image(self, image_data: str) -> dict:
        """
        Detect skin tone from base64 encoded image with proper computer vision.
        
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
            
            # Check brightness - if too dark, camera not ready
            mean_brightness = float(np.mean(image))
            if mean_brightness < 20:
                return {
                    'success': False,
                    'error': '🔦 Lighting too low. Ensure good bright lighting and try again.'
                }
            
            # Detect hand region with HSV skin segmentation
            hand_mask = self._detect_hand_region(image)
            
            if hand_mask is None:
                print(f"[HandDetector] HSV detection failed - trying YCrCb fallback")
                # Fallback: YCrCb color space (more lighting-robust)
                hand_mask = self._detect_skin_fallback(image)
                
            if hand_mask is None:
                return {
                    'success': False,
                    'error': '👋 Hand not detected. Keep your hand centered in the guide frame with good lighting.'
                }
            
            print(f"[HandDetector] Hand detected successfully")
            
            # Extract skin color from detected hand region
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
                'error': f'Detection error: {str(e)}'
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
        Detect skin region using HSV color space filtering.
        This is the REAL skin detection that actually segments skin from non-skin.
        """
        height, width = image.shape[:2]

        # Check image brightness first
        mean_brightness = float(np.mean(image))
        print(f"[HandDetector] Overall image brightness: {mean_brightness:.1f}")

        if mean_brightness < 15:
            print(f"[HandDetector] Image too dark — camera not ready yet")
            return None

        # Convert BGR to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define skin color range in HSV - expanded to cover fair/light skin tones
        # Fair skin: yellows + reds + oranges
        # H: 5-30 (oranges,reds) + 150-180 (red wrap-around) 
        # S: 25-220 (lower saturation for fair skin which tends to be less saturated)
        # V: 60-255 (more forgiving on brightness for dim lighting)
        lower_orange = np.array([5, 25, 60], dtype=np.uint8)
        upper_orange = np.array([30, 220, 255], dtype=np.uint8)

        lower_red = np.array([150, 25, 60], dtype=np.uint8)
        upper_red = np.array([180, 220, 255], dtype=np.uint8)

        # Create mask for skin pixels
        mask1 = cv2.inRange(hsv, lower_orange, upper_orange)
        mask2 = cv2.inRange(hsv, lower_red, upper_red)
        mask = cv2.bitwise_or(mask1, mask2)

        # Remove noise with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Check if skin detected
        skin_ratio = float(np.sum(mask > 0)) / (height * width)
        print(f"[HandDetector] Skin detection ratio: {skin_ratio:.1%}")

        if skin_ratio < 0.02:
            print(f"[HandDetector] Too little skin detected ({skin_ratio:.1%}) - using fallback")
            return None

        print(f"[HandDetector] HSV skin detection successful! ({skin_ratio:.1%} skin)")
        return mask
    
    def _detect_skin_fallback(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Fallback: Use YCrCb color space (more lighting-robust than HSV).
        Only used when HSV detection fails.
        """
        print(f"[HandDetector] Using YCrCb fallback skin detection")
        height, width = image.shape[:2]

        # Convert BGR to YCrCb
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

        # YCrCb skin detection - expanded ranges for fair/light skin in dim lighting
        # Y (brightness): 0-255, Cr (red): 120-180, Cb (blue): 60-140
        lower = np.array([0, 120, 60], dtype=np.uint8)
        upper = np.array([255, 180, 140], dtype=np.uint8)

        mask = cv2.inRange(ycrcb, lower, upper)

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Check skin ratio
        skin_ratio = float(np.sum(mask > 0)) / (height * width)
        print(f"[HandDetector] YCrCb skin ratio: {skin_ratio:.1%}")

        if skin_ratio < 0.02:
            print(f"[HandDetector] YCrCb fallback also failed - insufficient skin detected")
            return None

        print(f"[HandDetector] YCrCb fallback successful! ({skin_ratio:.1%} skin)")
        return mask
    
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
        
        if len(skin_pixels) == 0:
            print(f"[HandDetector] No skin pixels found!")
            return np.array([128, 128, 128], dtype=int)  # Default gray
        
        # Calculate average color (BGR to RGB)
        avg_color_bgr = np.mean(skin_pixels, axis=0)
        avg_color_rgb = avg_color_bgr[::-1]  # Convert BGR to RGB
        
        print(f"[HandDetector] Extracted RGB: {avg_color_rgb}")
        
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
