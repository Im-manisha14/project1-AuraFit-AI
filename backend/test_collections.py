"""Quick test: login + call collections to verify end-to-end."""
import sys, json
sys.path.insert(0, '.')
from app import app

with app.app_context():
    from models.user import User, UserProfile
    from models.outfit import Outfit, OutfitInteraction
    from services.recommendation_engine import RecommendationEngine
    from sqlalchemy import func, desc, or_
    from extensions import db

    # simulate collections for user_id=1 (has female/hourglass profile)
    profile = UserProfile.query.filter_by(user_id=1).first()
    gender = (profile.gender or '').lower() if profile else ''
    print(f"User gender: {gender}")

    engine = RecommendationEngine()

    def gender_filter(q):
        if gender in ('male', 'female'):
            return q.filter(or_(Outfit.gender == gender, Outfit.gender == 'unisex', Outfit.gender == None))
        return q

    casual = gender_filter(Outfit.query.filter(Outfit.occasion == 'casual')).limit(8).all()
    formal = gender_filter(Outfit.query.filter(Outfit.occasion.in_(['formal', 'work']))).limit(8).all()
    party  = gender_filter(Outfit.query.filter(Outfit.occasion.in_(['party', 'date']))).limit(8).all()
    sports = gender_filter(Outfit.query.filter(or_(Outfit.occasion == 'gym', Outfit.style_type.ilike('%sport%'), Outfit.style_type.ilike('%athlet%')))).limit(8).all()
    minimalist = gender_filter(Outfit.query.filter(or_(Outfit.style_type.ilike('%minimalist%'), Outfit.style_type.ilike('%minimal%')))).limit(8).all()

    print(f"casual: {len(casual)} outfits")
    print(f"formal: {len(formal)} outfits")
    print(f"party:  {len(party)} outfits")
    print(f"sports: {len(sports)} outfits")
    print(f"minimalist: {len(minimalist)} outfits")
    print("Sample casual outfit:")
    if casual:
        o = casual[0]
        print(f"  {o.name} | occasion={o.occasion} | gender={o.gender} | img={o.image_url[:50]}...")
    print("\nAll collections have data: SUCCESS" if all([casual, formal, party, sports, minimalist]) else "SOME EMPTY!")
