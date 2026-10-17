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
    print(f'User: {user.username if user else None}, Gender: {profile.gender if profile else None}')
    engine = RecommendationEngine()
    recs = engine.generate_recommendations(
        user=user,
        profile=profile,
        preferences=None,
        occasion='formal',
        season='all',
        gender='female',
        category='dress',
        limit=25
    )
    print(f'Generated {len(recs)} recommendations for formal:')
    for r in recs:
        outfit = r.get('outfit') or r
        print(f"  ID: {outfit.get('id')}, Title: {outfit.get('name') or outfit.get('title')}, Retailer: {outfit.get('retailer')}, Price: {outfit.get('price')}")
        print(f"     Image: {outfit.get('image_url')}")
        print(f"     Desc: {outfit.get('description')}")

    sims = getattr(engine, 'last_similar_recommendations', [])
    print(f'\nGenerated {len(sims)} similar recommendations:')
    for s in sims:
        outfit = s.get('outfit') or s
        print(f"  ID: {outfit.get('id')}, Title: {outfit.get('name') or outfit.get('title')}, Price: {outfit.get('price')}")
        print(f"     Image: {outfit.get('image_url')}")
