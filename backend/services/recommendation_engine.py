import numpy as np
from typing import List, Dict

class RecommendationEngine:
    """
    Core recommendation engine that combines multiple factors:
    - Body type compatibility
    - Style preferences
    - Fabric comfort
    - Trend analysis
    - User feedback history
    """
    
    def __init__(self):
        self.weights = {
            'body_type': 0.25,
            'style_match': 0.30,
            'comfort': 0.20,
            'trend': 0.15,
            'feedback': 0.10
        }
    
    def generate_recommendations(
        self,
        user: 'User',
        profile: 'UserProfile',
        preferences: 'StylePreference',
        occasion: str,
        season: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Generate personalized outfit recommendations
        """
        from extensions import db
        from models.outfit import Outfit, Recommendation
        
        # Get candidate outfits
        query = Outfit.query
        
        if occasion != 'all':
            query = query.filter_by(occasion=occasion)
        if season != 'all':
            query = query.filter_by(season=season)
        
        outfits = query.all()
        
        # Calculate scores for each outfit
        scored_outfits = []
        for outfit in outfits:
            scores = self._calculate_scores(outfit, profile, preferences)
            overall_score = self._calculate_overall_score(scores)
            
            scored_outfits.append({
                'outfit': outfit.to_dict(),
                'scores': scores,
                'overall_score': overall_score
            })
        
        # Sort by overall score
        scored_outfits.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Save recommendations to database
        top_recommendations = scored_outfits[:limit]
        for rec_data in top_recommendations:
            recommendation = Recommendation(
                user_id=user.id,
                outfit_id=rec_data['outfit']['id'],
                overall_score=rec_data['overall_score'],
                style_match_score=rec_data['scores']['style_match'],
                comfort_score=rec_data['scores']['comfort'],
                trend_score=rec_data['scores']['trend'],
                body_type_score=rec_data['scores']['body_type'],
                occasion=occasion,
                season=season
            )
            db.session.add(recommendation)
        
        db.session.commit()
        
        return top_recommendations
    
    def _calculate_scores(
        self,
        outfit: Outfit,
        profile: UserProfile,
        preferences: StylePreference
    ) -> Dict[str, float]:
        """
        Calculate individual scores for each factor
        """
        return {
            'body_type': self._calculate_body_type_score(outfit, profile),
            'style_match': self._calculate_style_match_score(outfit, preferences),
            'comfort': self._calculate_comfort_score(outfit, preferences),
            'trend': self._calculate_trend_score(outfit),
            'feedback': 0.5  # Placeholder, will be improved with ML
        }
    
    def _calculate_body_type_score(self, outfit: Outfit, profile: UserProfile) -> float:
        """
        Score based on body type compatibility
        """
        body_type_mapping = {
            'hourglass': ['fitted', 'wrap', 'belted'],
            'pear': ['a-line', 'bootcut', 'wide-leg'],
            'apple': ['empire', 'v-neck', 'straight'],
            'rectangle': ['peplum', 'ruffled', 'layered'],
            'inverted_triangle': ['wide-leg', 'flared', 'bootcut']
        }
        
        if not profile.body_type:
            return 0.5
        
        suitable_styles = body_type_mapping.get(profile.body_type, [])
        
        # Check if outfit style matches body type
        if outfit.style_type and any(style in outfit.style_type.lower() for style in suitable_styles):
            return 0.9
        
        return 0.5
    
    def _calculate_style_match_score(self, outfit: Outfit, preferences: StylePreference) -> float:
        """
        Score based on user style preferences
        """
        if not preferences:
            return 0.5
        
        score = 0.0
        count = 0
        
        # Check color preferences
        if preferences.preferred_colors and outfit.colors:
            color_match = any(color in outfit.colors for color in preferences.preferred_colors)
            score += 1.0 if color_match else 0.3
            count += 1
        
        # Check style preferences
        if preferences.preferred_styles and outfit.style_type:
            style_match = outfit.style_type in preferences.preferred_styles
            score += 1.0 if style_match else 0.3
            count += 1
        
        return score / count if count > 0 else 0.5
    
    def _calculate_comfort_score(self, outfit: Outfit, preferences: StylePreference) -> float:
        """
        Score based on fabric comfort prediction
        """
        if outfit.comfort_score:
            return outfit.comfort_score
        
        # Use ML model in future
        return 0.7
    
    def _calculate_trend_score(self, outfit: Outfit) -> float:
        """
        Score based on current fashion trends
        """
        if outfit.is_trending:
            return outfit.trend_score if outfit.trend_score else 0.8
        
        return 0.5
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted overall score
        """
        overall = 0.0
        for factor, score in scores.items():
            overall += score * self.weights.get(factor, 0.0)
        
        return round(overall, 2)
