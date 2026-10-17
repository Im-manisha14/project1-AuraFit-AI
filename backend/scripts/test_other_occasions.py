import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.user import User, UserProfile
from services.recommendation_engine import RecommendationEngine

app = create_app()
with app.app_context():
    user = User.query.filter_by(id=3).first()
    profile = UserProfile.query.filter_by(user_id=user.id).first() if user else None
    engine = RecommendationEngine()
    
    for occ in ['formal', 'casual', 'party', 'office', 'wedding']:
        recs = engine.generate_recommendations(
            user=user,
            profile=profile,
            preferences=None,
            occasion=occ,
            season='all',
            gender='female',
            category='dress',
            limit=5
        )
        print(f"Occasion '{occ}' returned {len(recs)} items:")
        for r in recs[:3]:
            o = r.get('outfit') or r
            title = o.get('name') or o.get('title')
            img = o.get('image_url') or ''
            print(f"  - {title} | {img[:50]}")
        print()
