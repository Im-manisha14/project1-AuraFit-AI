import sys
sys.path.insert(0, '.')
from app import app
with app.app_context():
    from models.outfit import Outfit
    from models.user import UserProfile, StylePreference, User
    from services.recommendation_engine import RecommendationEngine

    profile = UserProfile.query.first()
    if not profile:
        print('No profile found')
    else:
        prefs = StylePreference.query.filter_by(user_id=profile.user_id).first()
        user = User.query.get(profile.user_id)
        print(f"User: {user.username}, gender={profile.gender}, body_type={profile.body_type}")
        engine = RecommendationEngine()
        try:
            results = engine.generate_recommendations(
                user=user, profile=profile, preferences=prefs,
                occasion='formal', season='all', limit=5
            )
            print(f'Got {len(results)} results for formal:')
            for r in results:
                score = r['overall_score']
                name = r['outfit']['name']
                occ = r['outfit']['occasion']
                gen = r['outfit']['gender']
                print(f'  [{score}] {name} | occasion={occ} | gender={gen}')
        except Exception as e:
            import traceback
            traceback.print_exc()
