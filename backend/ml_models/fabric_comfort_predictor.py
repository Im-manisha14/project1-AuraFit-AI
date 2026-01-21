import numpy as np
from typing import Dict, List

class FabricComfortPredictor:
    """
    Predicts fabric comfort based on:
    - Fabric type
    - Weather/season
    - Activity level
    - User preferences
    """
    
    def __init__(self):
        # Fabric properties (breathability, softness, stretchability, warmth)
        self.fabric_properties = {
            'cotton': {'breathability': 0.9, 'softness': 0.8, 'stretch': 0.3, 'warmth': 0.5},
            'polyester': {'breathability': 0.4, 'softness': 0.5, 'stretch': 0.6, 'warmth': 0.4},
            'wool': {'breathability': 0.7, 'softness': 0.6, 'stretch': 0.3, 'warmth': 0.9},
            'silk': {'breathability': 0.8, 'softness': 0.9, 'stretch': 0.2, 'warmth': 0.4},
            'linen': {'breathability': 1.0, 'softness': 0.6, 'stretch': 0.2, 'warmth': 0.3},
            'denim': {'breathability': 0.5, 'softness': 0.4, 'stretch': 0.5, 'warmth': 0.6},
            'spandex': {'breathability': 0.3, 'softness': 0.6, 'stretch': 1.0, 'warmth': 0.3},
            'rayon': {'breathability': 0.7, 'softness': 0.8, 'stretch': 0.4, 'warmth': 0.4},
            'nylon': {'breathability': 0.3, 'softness': 0.5, 'stretch': 0.7, 'warmth': 0.4},
            'leather': {'breathability': 0.2, 'softness': 0.3, 'stretch': 0.1, 'warmth': 0.8}
        }
        
        # Season requirements
        self.season_requirements = {
            'summer': {'breathability': 1.0, 'softness': 0.6, 'stretch': 0.5, 'warmth': 0.1},
            'winter': {'breathability': 0.4, 'softness': 0.7, 'stretch': 0.5, 'warmth': 1.0},
            'spring': {'breathability': 0.7, 'softness': 0.7, 'stretch': 0.5, 'warmth': 0.5},
            'fall': {'breathability': 0.6, 'softness': 0.7, 'stretch': 0.5, 'warmth': 0.7},
            'all': {'breathability': 0.6, 'softness': 0.7, 'stretch': 0.5, 'warmth': 0.5}
        }
    
    def predict_comfort(self, fabrics: List[str], season: str = 'all',
                       activity_level: str = 'moderate') -> float:
        """
        Predict comfort score for given fabrics and conditions
        
        Args:
            fabrics: List of fabric types
            season: Season (summer, winter, spring, fall, all)
            activity_level: low, moderate, high
        
        Returns:
            Comfort score (0-1)
        """
        if not fabrics:
            return 0.5
        
        # Get season requirements
        season_req = self.season_requirements.get(season, self.season_requirements['all'])
        
        # Activity level weights
        activity_weights = {
            'low': {'breathability': 0.3, 'softness': 0.4, 'stretch': 0.2, 'warmth': 0.1},
            'moderate': {'breathability': 0.3, 'softness': 0.3, 'stretch': 0.2, 'warmth': 0.2},
            'high': {'breathability': 0.5, 'softness': 0.2, 'stretch': 0.2, 'warmth': 0.1}
        }
        
        weights = activity_weights.get(activity_level, activity_weights['moderate'])
        
        # Calculate comfort for each fabric
        fabric_scores = []
        for fabric in fabrics:
            fabric = fabric.lower().strip()
            if fabric not in self.fabric_properties:
                fabric_scores.append(0.5)  # Unknown fabric
                continue
            
            props = self.fabric_properties[fabric]
            
            # Calculate weighted score
            score = 0.0
            for prop, value in props.items():
                season_match = 1 - abs(value - season_req[prop])
                score += season_match * weights[prop]
            
            fabric_scores.append(score)
        
        # Return average comfort score
        return round(np.mean(fabric_scores), 2)
    
    def get_fabric_analysis(self, fabric: str) -> Dict:
        """
        Get detailed analysis of a fabric type
        """
        fabric = fabric.lower().strip()
        if fabric not in self.fabric_properties:
            return {'error': 'Unknown fabric type'}
        
        props = self.fabric_properties[fabric]
        
        # Best seasons
        best_seasons = []
        for season, req in self.season_requirements.items():
            if season == 'all':
                continue
            match_score = self._calculate_season_match(props, req)
            if match_score > 0.7:
                best_seasons.append(season)
        
        return {
            'fabric': fabric,
            'properties': props,
            'best_seasons': best_seasons if best_seasons else ['all'],
            'best_for': self._get_best_use_cases(props)
        }
    
    def _calculate_season_match(self, props: Dict, season_req: Dict) -> float:
        """Calculate how well fabric matches season requirements"""
        match_score = 0.0
        for prop, value in props.items():
            match_score += 1 - abs(value - season_req[prop])
        return match_score / len(props)
    
    def _get_best_use_cases(self, props: Dict) -> List[str]:
        """Determine best use cases for fabric"""
        use_cases = []
        
        if props['breathability'] > 0.7:
            use_cases.append('activewear')
        if props['softness'] > 0.7:
            use_cases.append('casual-wear')
        if props['warmth'] > 0.7:
            use_cases.append('winter-wear')
        if props['stretch'] > 0.7:
            use_cases.append('sportswear')
        
        return use_cases if use_cases else ['general-wear']
