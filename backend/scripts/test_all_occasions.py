import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from services.recommendation_engine import RecommendationEngine
from models.user import User, UserProfile, StylePreference

def test_all_occasions():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email='test_female_contract@aurafit.com').first()
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        prefs = StylePreference.query.filter_by(user_id=user.id).first()
        engine = RecommendationEngine()

        occasions = ['formal', 'casual', 'party', 'wedding', 'office', 'date', 'traditional', 'evening']
        print("\nTesting recommendation generation across occasions:")
        for occ in occasions:
            recs = engine.generate_recommendations(
                user=user,
                profile=profile,
                preferences=prefs,
                occasion=occ,
                season='all',
                limit=10,
                gender='female',
                category='dress'
            )
            print(f"Occasion '{occ}': {len(recs)} recommendations returned")
            for r in recs[:2]:
                outfit = r.get('outfit') or r
                print(f"   -> [{outfit.get('occasion')}] {outfit.get('title') or outfit.get('name')} (Match: {r.get('overall_score')})")

if __name__ == '__main__':
    test_all_occasions()
