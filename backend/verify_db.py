import os
import sys
from app import create_app
from extensions import db
from models.user import User, UserProfile, StylePreference
from services.recommendation_engine import RecommendationEngine

app = create_app()
with app.app_context():
    # Pick first user
    user_record = User.query.first()
    if not user_record:
        print("No users found.")
        sys.exit(0)
    
    profile = UserProfile.query.filter_by(user_id=user_record.id).first()
    prefs = StylePreference.query.filter_by(user_id=user_record.id).first()
    engine = RecommendationEngine()
    recs = engine.generate_recommendations(user=user_record, profile=profile, preferences=prefs, occasion='all', season='all', limit=5)
    
    print(f"Generated {len(recs)} recommendations.")
    for i, r in enumerate(recs):
        print(f"{i+1}. {r['outfit']['name']} | URL: {r['outfit']['product_url']} | Image: {r['outfit']['image_url']}")
