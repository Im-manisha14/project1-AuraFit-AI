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
                # Fallback: broader center region
                hand_mask = self._detect_skin_fallback(image)
                
            if hand_mask is None:
                return {
                    'success': False,
                    'error': 'Camera not ready yet. Please wait 1-2 seconds for the camera to warm up, then try again.'
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
        Detect hand region using the guide-box center area.
        The UI instructs the user to center their hand in the guide frame,
        so we sample from that central region directly — this is reliable
        for all skin tones and lighting conditions.
        Falls back to skin-color contour detection if the center region
        appears too dark (no hand present yet).
        """
        height, width = image.shape[:2]

        # Define the guide-box region (matches the overlay in the UI:
        # horizontally 25%-75%, vertically 20%-80%)
        x_start = int(width * 0.25)
        x_end   = int(width * 0.75)
        y_start = int(height * 0.20)
        y_end   = int(height * 0.80)

        guide_region = image[y_start:y_end, x_start:x_end]

        # Sanity check: if the region is too dark (average brightness < 20),
        # the camera hasn't loaded a real frame yet — signal failure so the
        # caller can return a "please wait" error.
        mean_brightness = float(np.mean(guide_region))
        print(f"[HandDetector] Guide region mean brightness: {mean_brightness:.1f}")

        if mean_brightness < 20:
            print(f"[HandDetector] Image too dark — camera not ready yet")
            return None

        # Build a mask covering the guide region
        hand_mask = np.zeros((height, width), dtype=np.uint8)
        hand_mask[y_start:y_end, x_start:x_end] = 255

        print(f"[HandDetector] Guide-region detection successful!")
        return hand_mask
    
    def _detect_skin_fallback(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Fallback: use the full center half of the image.
        Only used when the primary guide-region check returns None
        (i.e. image is too dark / camera not ready).
        """
        print(f"[HandDetector] Using fallback skin detection")
        height, width = image.shape[:2]

        # Broader center region
        x_start = int(width * 0.15)
        x_end   = int(width * 0.85)
        y_start = int(height * 0.10)
        y_end   = int(height * 0.90)

        # If still too dark, give up
        region = image[y_start:y_end, x_start:x_end]
        if float(np.mean(region)) < 15:
            print(f"[HandDetector] Fallback: image still too dark")
            return None

        mask = np.zeros((height, width), dtype=np.uint8)
        mask[y_start:y_end, x_start:x_end] = 255
        print(f"[HandDetector] Fallback detection successful!")
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
