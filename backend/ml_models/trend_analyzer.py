import numpy as np
from typing import Dict, List
from datetime import datetime

class TrendAnalyzer:
    """
    Analyzes fashion trends and predicts trend scores
    In production, this would connect to fashion APIs and social media
    """
    
    def __init__(self):
        # Mock trend data (in production, fetch from APIs)
        self.current_trends = {
            '2026': {
                'colors': ['sage-green', 'lavender', 'terracotta', 'navy', 'cream'],
                'styles': ['oversized', 'minimalist', 'sustainable', 'vintage', 'athleisure'],
                'patterns': ['geometric', 'floral', 'abstract', 'monochrome', 'tie-dye'],
                'materials': ['organic-cotton', 'recycled-polyester', 'linen', 'hemp']
            }
        }
        
        # Trend scores by category
        self.trend_weights = {
            'color_trend': 0.3,
            'style_trend': 0.4,
            'pattern_trend': 0.2,
            'material_trend': 0.1
        }
    
    def analyze_outfit_trend(self, outfit_data: Dict) -> Dict:
        """
        Analyze how trendy an outfit is
        
        Args:
            outfit_data: Dictionary with colors, style_type, patterns, fabric_types
        
        Returns:
            Dictionary with trend score and analysis
        """
        current_year = str(datetime.now().year)
        trends = self.current_trends.get(current_year, self.current_trends['2026'])
        
        scores = {}
        
        # Analyze colors
        if outfit_data.get('colors'):
            scores['color_trend'] = self._calculate_color_trend(
                outfit_data['colors'], trends['colors']
            )
        else:
            scores['color_trend'] = 0.5
        
        # Analyze style
        if outfit_data.get('style_type'):
            scores['style_trend'] = self._calculate_style_trend(
                outfit_data['style_type'], trends['styles']
            )
        else:
            scores['style_trend'] = 0.5
        
        # Analyze patterns (if available)
        patterns = outfit_data.get('patterns', [])
        scores['pattern_trend'] = self._calculate_pattern_trend(
            patterns, trends['patterns']
        )
        
        # Analyze materials
        if outfit_data.get('fabric_types'):
            scores['material_trend'] = self._calculate_material_trend(
                outfit_data['fabric_types'], trends['materials']
            )
        else:
            scores['material_trend'] = 0.5
        
        # Calculate overall trend score
        overall_score = sum(
            scores[key] * self.trend_weights[key]
            for key in scores
        )
        
        return {
            'overall_trend_score': round(overall_score, 2),
            'is_trending': overall_score > 0.7,
            'trend_breakdown': scores,
            'trending_elements': self._identify_trending_elements(outfit_data, trends)
        }
    
    def _calculate_color_trend(self, outfit_colors: List, trending_colors: List) -> float:
        """Calculate color trend score"""
        if not outfit_colors:
            return 0.5
        
        matches = sum(1 for color in outfit_colors if color.lower() in trending_colors)
        return min(matches / len(outfit_colors), 1.0)
    
    def _calculate_style_trend(self, style: str, trending_styles: List) -> float:
        """Calculate style trend score"""
        style_lower = style.lower()
        
        for trend_style in trending_styles:
            if trend_style in style_lower or style_lower in trend_style:
                return 0.9
        
        return 0.4
    
    def _calculate_pattern_trend(self, patterns: List, trending_patterns: List) -> float:
        """Calculate pattern trend score"""
        if not patterns:
            return 0.5
        
        matches = sum(1 for pattern in patterns if pattern.lower() in trending_patterns)
        return min(matches / len(patterns) if patterns else 0.5, 1.0)
    
    def _calculate_material_trend(self, materials: List, trending_materials: List) -> float:
        """Calculate material/fabric trend score"""
        if not materials:
            return 0.5
        
        matches = sum(
            1 for material in materials
            if any(trend in material.lower() for trend in trending_materials)
        )
        return min(matches / len(materials), 1.0)
    
    def _identify_trending_elements(self, outfit_data: Dict, trends: Dict) -> List[str]:
        """Identify which elements of the outfit are trending"""
        trending = []
        
        # Check colors
        if outfit_data.get('colors'):
            for color in outfit_data['colors']:
                if color.lower() in trends['colors']:
                    trending.append(f"color: {color}")
        
        # Check style
        if outfit_data.get('style_type'):
            style = outfit_data['style_type'].lower()
            for trend_style in trends['styles']:
                if trend_style in style:
                    trending.append(f"style: {trend_style}")
        
        # Check materials
        if outfit_data.get('fabric_types'):
            for material in outfit_data['fabric_types']:
                for trend_mat in trends['materials']:
                    if trend_mat in material.lower():
                        trending.append(f"material: {trend_mat}")
        
        return trending
    
    def get_current_trends(self) -> Dict:
        """Get current fashion trends"""
        current_year = str(datetime.now().year)
        return self.current_trends.get(current_year, self.current_trends['2026'])
