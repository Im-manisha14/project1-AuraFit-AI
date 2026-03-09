from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('recommendation', __name__, url_prefix='/api/recommendations')

@bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_recommendations():
    from models.user import User, UserProfile, StylePreference
    from services.recommendation_engine import RecommendationEngine
    
    try:
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
        data = request.get_json()
        
        # Get user data
        user = User.query.get(user_id)
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        preferences = StylePreference.query.filter_by(user_id=user_id).first()
        
        if not profile:
            return jsonify({'error': 'Please complete your profile first'}), 400
        
        # Get parameters
        occasion = data.get('occasion', 'casual')
        season = data.get('season', 'all')
        limit = data.get('limit', 10)
        
        # Initialize recommendation engine
        engine = RecommendationEngine()
        
        # Generate recommendations
        recommendations = engine.generate_recommendations(
            user=user,
            profile=profile,
            preferences=preferences,
            occasion=occasion,
            season=season,
            limit=limit
        )
        
        return jsonify({
            'recommendations': recommendations,
            'count': len(recommendations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/track', methods=['POST'])
@jwt_required()
def track_interaction():
    """
    Record a user interaction with an outfit.
    Used by the collaborative filtering layer.

    Body JSON:
        outfit_id        (int, required)
        interaction_type (str, optional) – 'view' | 'click' | 'save'  default 'view'
    """
    from models.outfit import OutfitInteraction
    from extensions import db

    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        outfit_id = data.get('outfit_id')
        if not outfit_id:
            return jsonify({'error': 'outfit_id is required'}), 400

        interaction_type = data.get('interaction_type', 'view')
        if interaction_type not in ('view', 'click', 'save'):
            interaction_type = 'view'

        interaction = OutfitInteraction(
            user_id=user_id,
            outfit_id=int(outfit_id),
            interaction_type=interaction_type,
        )
        db.session.add(interaction)
        db.session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        from extensions import db
        db.session.rollback()
        print(f'[track] error: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/collections', methods=['GET'])
@jwt_required()
def get_collections():
    """
    Return multiple curated outfit collections for the discovery page.
    Each collection is a list of outfit dicts with shopping_links attached.

    Query params:
      season  – 'summer'|'winter'|'spring'|'fall'|'all'  (default 'all')
      limit   – per-collection cap, default 12
    """
    from models.outfit import Outfit, OutfitInteraction
    from models.user import UserProfile
    from services.recommendation_engine import RecommendationEngine
    from extensions import db
    from sqlalchemy import func, desc, or_

    try:
        user_id = int(get_jwt_identity())
        season  = request.args.get('season', 'all')
        limit   = min(int(request.args.get('limit', 12)), 20)

        # Determine gender from user profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        gender  = (profile.gender or '').lower() if profile else ''

        engine = RecommendationEngine()

        def gender_filter(query):
            if gender in ('male', 'female'):
                return query.filter(
                    or_(
                        Outfit.gender == gender,
                        Outfit.gender == 'unisex',
                        Outfit.gender.is_(None),
                    )
                )
            return query

        def attach_links(outfits):
            result = []
            for o in outfits:
                d = o.to_dict()
                d['shopping_links'] = engine._generate_shopping_links(o, gender)
                result.append(d)
            return result

        from sqlalchemy import func as sqlfunc
        import random

        # ── 1. Trending ── most interaction events first ──────────────────
        interaction_counts = (
            db.session.query(
                OutfitInteraction.outfit_id,
                func.count(OutfitInteraction.id).label('cnt'),
            )
            .group_by(OutfitInteraction.outfit_id)
            .subquery()
        )
        trending_q = (
            db.session.query(Outfit)
            .outerjoin(interaction_counts, Outfit.id == interaction_counts.c.outfit_id)
            .order_by(desc(interaction_counts.c.cnt), desc(Outfit.trend_score), desc(Outfit.id))
        )
        if gender in ('male', 'female'):
            trending_q = trending_q.filter(
                or_(Outfit.gender == gender, Outfit.gender == 'unisex', Outfit.gender.is_(None))
            )
        trending = attach_links(trending_q.limit(limit).all())
        # fallback when no interaction data yet: order by trend_score desc so
        # we don't always get the lowest IDs
        if len(trending) < 4:
            trending = attach_links(
                gender_filter(Outfit.query)
                .order_by(desc(Outfit.trend_score), desc(Outfit.id))
                .limit(limit).all()
            )

        # ── 2. Seasonal Picks ─────────────────────────────────────────────
        if season and season != 'all':
            seasonal_q = gender_filter(
                Outfit.query.filter(
                    or_(Outfit.season == season, Outfit.season == 'all')
                )
            )
        else:
            seasonal_q = gender_filter(Outfit.query)
        # Order by created_at desc so newest outfits surface first
        seasonal = attach_links(seasonal_q.order_by(desc(Outfit.created_at)).limit(limit).all())

        # ── 3. Casual Collection ──────────────────────────────────────────
        casual = attach_links(
            gender_filter(Outfit.query.filter(Outfit.occasion == 'casual'))
            .order_by(Outfit.id)
            .limit(limit).all()
        )

        # ── 4. Formal & Work Wear ─────────────────────────────────────────
        formal = attach_links(
            gender_filter(
                Outfit.query.filter(Outfit.occasion.in_(['formal', 'work']))
            )
            .order_by(desc(Outfit.trend_score), Outfit.id)
            .limit(limit).all()
        )

        # ── 5. Sports & Athleisure ────────────────────────────────────────
        sports = attach_links(
            gender_filter(
                Outfit.query.filter(
                    or_(
                        Outfit.occasion == 'gym',
                        Outfit.style_type.ilike('%sport%'),
                        Outfit.style_type.ilike('%athlet%'),
                    )
                )
            )
            .order_by(Outfit.id)
            .limit(limit).all()
        )

        # ── 6. Minimalist Fashion ─────────────────────────────────────────
        minimalist = attach_links(
            gender_filter(
                Outfit.query.filter(
                    or_(
                        Outfit.style_type.ilike('%minimalist%'),
                        Outfit.style_type.ilike('%minimal%'),
                    )
                )
            )
            .order_by(desc(Outfit.id))
            .limit(limit).all()
        )

        # ── 7. Party & Date Night ─────────────────────────────────────────
        party = attach_links(
            gender_filter(
                Outfit.query.filter(Outfit.occasion.in_(['party', 'date']))
            )
            .order_by(desc(Outfit.trend_score), desc(Outfit.id))
            .limit(limit).all()
        )

        # ── 8. Based on Skin Tone ─────────────────────────────────────────
        # Pull outfits whose color palette matches the user's skin tone,
        # spread across all occasions so the row isn't dominated by one type.
        skin_tone_outfits = []
        if profile and profile.skin_tone:
            from services.recommendation_engine import SKIN_TONE_COMPATIBLE_COLORS
            compatible_colors = SKIN_TONE_COMPATIBLE_COLORS.get(
                profile.skin_tone.lower(), []
            )
            if compatible_colors:
                # Fetch ALL gender-appropriate outfits (no occasion restriction)
                all_outfits = gender_filter(Outfit.query).order_by(Outfit.occasion, Outfit.id).all()
                matched = []
                for o in all_outfits:
                    if not o.colors:
                        continue
                    outfit_colors = [c.lower() for c in o.colors]
                    if any(
                        any(comp in oc or oc in comp for comp in compatible_colors)
                        for oc in outfit_colors
                    ):
                        matched.append(o)
                # Shuffle to surface a variety of occasions each time
                random.shuffle(matched)
                skin_tone_outfits = attach_links(matched[:limit])

        # ── 9. For Your Body Shape ────────────────────────────────────────
        body_shape_outfits = []
        if profile and profile.body_type:
            body_type = profile.body_type.lower()
            # Order by occasion so results are evenly spread
            all_outfits = gender_filter(Outfit.query).order_by(Outfit.occasion, desc(Outfit.id)).all()
            matched = []
            for o in all_outfits:
                if not o.body_type_compatibility:
                    continue
                compat = [bt.lower() for bt in o.body_type_compatibility]
                if 'all' in compat or body_type in compat:
                    matched.append(o)
            body_shape_outfits = attach_links(matched[:limit])

        return jsonify({
            'trending':   trending,
            'seasonal':   seasonal,
            'casual':     casual,
            'formal':     formal,
            'sports':     sports,
            'minimalist': minimalist,
            'party':      party,
            'skin_tone':  skin_tone_outfits,
            'body_shape': body_shape_outfits,
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
@jwt_required()
def get_recommendation_history():
    from models.outfit import Recommendation
    
    try:
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
        if not user_id:
            return jsonify({'error': 'Invalid token'}), 401
            
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        recommendations = Recommendation.query.filter_by(user_id=user_id)\
            .order_by(Recommendation.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'recommendations': [rec.to_dict() for rec in recommendations.items],
            'total': recommendations.total,
            'pages': recommendations.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:recommendation_id>', methods=['GET'])
@jwt_required()
def get_recommendation(recommendation_id):
    from models.outfit import Recommendation
    
    try:
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
        
        recommendation = Recommendation.query.filter_by(
            id=recommendation_id,
            user_id=user_id
        ).first()
        
        if not recommendation:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        return jsonify({'recommendation': recommendation.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
