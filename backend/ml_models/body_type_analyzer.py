import numpy as np
from typing import Dict, Tuple

class BodyTypeAnalyzer:
    """
    Analyzes user body measurements and determines body type
    Body types: hourglass, pear, apple, rectangle, inverted_triangle
    """
    
    def __init__(self):
        self.body_types = [
            'hourglass',
            'pear',
            'apple',
            'rectangle',
            'inverted_triangle'
        ]
    
    def analyze(self, height: float, weight: float, 
                bust: float = None, waist: float = None, 
                hips: float = None) -> Tuple[str, Dict]:
        """
        Analyze body measurements and determine body type
        
        Args:
            height: Height in cm
            weight: Weight in kg
            bust: Bust circumference in cm (optional)
            waist: Waist circumference in cm (optional)
            hips: Hips circumference in cm (optional)
        
        Returns:
            Tuple of (body_type, confidence_scores)
        """
        # Calculate BMI
        bmi = self._calculate_bmi(height, weight)
        
        # If detailed measurements available, use ratio-based analysis
        if all([bust, waist, hips]):
            return self._analyze_with_measurements(bust, waist, hips)
        
        # Otherwise, use simplified analysis
        return self._analyze_simplified(height, weight, bmi)
    
    def _calculate_bmi(self, height: float, weight: float) -> float:
        """Calculate BMI"""
        height_m = height / 100  # Convert cm to meters
        return weight / (height_m ** 2)
    
    def _analyze_with_measurements(self, bust: float, waist: float, 
                                   hips: float) -> Tuple[str, Dict]:
        """
        Detailed analysis using bust-waist-hip measurements
        """
        # Calculate ratios
        bust_waist = bust / waist if waist > 0 else 0
        hip_waist = hips / waist if waist > 0 else 0
        bust_hip = bust / hips if hips > 0 else 0
        
        scores = {}
        
        # Hourglass: bust and hips similar, waist significantly smaller
        if abs(bust - hips) <= 5 and hip_waist >= 1.25:
            scores['hourglass'] = 0.9
        else:
            scores['hourglass'] = 0.1
        
        # Pear: hips significantly larger than bust
        if hips > bust + 5 and hip_waist >= 1.25:
            scores['pear'] = 0.9
        else:
            scores['pear'] = 0.2
        
        # Apple: bust larger than hips, waist similar to bust
        if bust > hips + 5 and bust_waist < 1.2:
            scores['apple'] = 0.9
        else:
            scores['apple'] = 0.2
        
        # Rectangle: all measurements relatively similar
        if abs(bust - hips) <= 5 and abs(bust - waist) <= 10:
            scores['rectangle'] = 0.85
        else:
            scores['rectangle'] = 0.2
        
        # Inverted triangle: bust larger than hips, defined waist
        if bust > hips + 5 and bust_waist >= 1.2:
            scores['inverted_triangle'] = 0.85
        else:
            scores['inverted_triangle'] = 0.2
        
        # Determine primary body type
        body_type = max(scores, key=scores.get)
        
        return body_type, scores
    
    def _analyze_simplified(self, height: float, weight: float, 
                           bmi: float) -> Tuple[str, Dict]:
        """
        Simplified analysis without detailed measurements
        Returns reasonable default distribution
        """
        # For simplified analysis, return balanced scores
        scores = {
            'hourglass': 0.25,
            'pear': 0.20,
            'apple': 0.20,
            'rectangle': 0.20,
            'inverted_triangle': 0.15
        }
        
        # Slight adjustments based on BMI
        if bmi < 18.5:
            scores['rectangle'] += 0.15
        elif bmi > 25:
            scores['apple'] += 0.10
        
        body_type = max(scores, key=scores.get)
        
        return body_type, scores
    
    def get_recommendations_for_body_type(self, body_type: str) -> Dict:
        """
        Get style recommendations for specific body type
        """
        recommendations = {
            'hourglass': {
                'tops': ['fitted', 'wrap', 'v-neck', 'belted'],
                'bottoms': ['high-waisted', 'pencil-skirt', 'bootcut'],
                'avoid': ['baggy', 'oversized', 'boxy']
            },
            'pear': {
                'tops': ['embellished', 'bright-colors', 'boat-neck'],
                'bottoms': ['a-line', 'bootcut', 'wide-leg', 'dark-colors'],
                'avoid': ['tight-pants', 'skinny-jeans', 'tapered']
            },
            'apple': {
                'tops': ['empire-waist', 'v-neck', 'wrap'],
                'bottoms': ['straight-leg', 'bootcut', 'wide-leg'],
                'avoid': ['tight-waist', 'crop-tops', 'horizontal-stripes']
            },
            'rectangle': {
                'tops': ['peplum', 'ruffled', 'layered', 'belted'],
                'bottoms': ['flared', 'pleated', 'low-rise'],
                'avoid': ['boxy', 'straight', 'shapeless']
            },
            'inverted_triangle': {
                'tops': ['v-neck', 'scoop-neck', 'dark-colors'],
                'bottoms': ['wide-leg', 'flared', 'bright-colors', 'patterns'],
                'avoid': ['shoulder-pads', 'boat-neck', 'cap-sleeves']
            }
        }
        
        return recommendations.get(body_type, {})
