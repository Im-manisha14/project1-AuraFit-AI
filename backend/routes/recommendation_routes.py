from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('recommendation', __name__, url_prefix='/api/recommendations')

@bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_recommendations():
    from models.user import User, UserProfile, StylePreference
    from services.recommendation_engine import RecommendationEngine
    from extensions import db
    
    try:
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
        data = request.get_json()
        
        # Get user data
        user = db.session.get(User, user_id)
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        preferences = StylePreference.query.filter_by(user_id=user_id).first()
        
        if not profile:
            return jsonify({'error': 'Please complete your profile first'}), 400
        
        # Get parameters
        occasion = data.get('occasion', 'casual')
        season = data.get('season', 'all')
        limit = int(data.get('results') or data.get('limit') or 25)
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        price_range = data.get('price_range')
        retailer = data.get('retailer')
        
        # Initialize recommendation engine
        engine = RecommendationEngine()
        
        # Generate recommendations
        recommendations = engine.generate_recommendations(
            user=user,
            profile=profile,
            preferences=preferences,
            occasion=occasion,
            season=season,
            limit=limit,
            min_price=min_price,
            max_price=max_price,
            price_range=price_range,
            retailer=retailer
        )
        similar = getattr(engine, 'last_similar_recommendations', [])
        
        return jsonify({
            'recommendations': recommendations,
            'similar_recommendations': similar,
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
        from services.shopping_service import ProductValidator
        raw_gender = (profile.gender or '').lower() if profile else ''
        gender = ProductValidator.normalize_gender(raw_gender)

        engine = RecommendationEngine()

        def gender_filter(query):
            query = query.filter(
                Outfit.source.like('serpapi%'),
                Outfit.in_stock == True,
                Outfit.image_url.isnot(None),
                Outfit.image_url != '',
                ~Outfit.image_url.like('%1V2w3X4y5%'),
                ~Outfit.image_url.like('%dummy%'),
                ~Outfit.image_url.like('%placeholder%'),
                Outfit.product_url.isnot(None),
                Outfit.product_url != ''
            )
            if gender == 'female':
                return query.filter(Outfit.gender == 'female', Outfit.category == 'dress')
            elif gender == 'male':
                return query.filter(Outfit.gender == 'male', Outfit.category != 'dress')
            return query

        import re

        # Global deduplication across all collection carousels on the dashboard
        seen_global_col_imgs = set()
        seen_global_col_urls = set()
        seen_global_col_ids = set()

        def attach_links(outfits, max_items=limit):
            result = []
            for o in outfits:
                # 1. Product & category validation (Section 18 & 19)
                prod_dict = {'title': o.name, 'description': o.description or '', 'category': o.category or ''}
                if gender == 'female':
                    is_dress, _, _ = ProductValidator.is_actual_dress(prod_dict)
                    if not is_dress:
                        continue
                is_compat, _, _ = ProductValidator.is_gender_compatible(prod_dict, gender)
                if not is_compat:
                    continue

                # 2. Image validation & global cross-collection deduplication
                img = (o.image_url or '').strip()
                if not img or '1V2w3X4y5' in img or 'dummy' in img or 'placeholder' in img:
                    continue
                tbn_m = re.search(r'q=tbn:([^&]+)', img)
                img_k = tbn_m.group(1) if tbn_m else img.split('?')[0].strip()
                if img_k in seen_global_col_imgs:
                    continue

                # 3. Canonical URL & ID deduplication
                url = (o.product_url or '').strip()
                canon_u = ProductValidator.canonicalize_url(url) if url else ''
                if canon_u and canon_u in seen_global_col_urls:
                    continue

                cid = f"{o.store or ''}:{o.external_id or canon_u or o.name}"
                if cid in seen_global_col_ids:
                    continue

                seen_global_col_imgs.add(img_k)
                if canon_u:
                    seen_global_col_urls.add(canon_u)
                seen_global_col_ids.add(cid)

                d = o.to_dict()
                d['shopping_links'] = engine._generate_shopping_links(o, gender)
                if o.product_url:
                    d['exact_product_link_available'] = True
                    d['shopping_url'] = canon_u or o.product_url
                else:
                    d['shopping_url'] = None
                result.append(d)
                if len(result) >= max_items:
                    break
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
            gender_filter(db.session.query(Outfit))
            .outerjoin(interaction_counts, Outfit.id == interaction_counts.c.outfit_id)
            .order_by(desc(interaction_counts.c.cnt), desc(Outfit.trend_score), desc(Outfit.id))
        )
        trending = attach_links(trending_q.limit(limit * 2).all())
        # fallback when no interaction data yet: order by trend_score desc
        if len(trending) < 4:
            trending = attach_links(
                gender_filter(Outfit.query)
                .order_by(desc(Outfit.trend_score), desc(Outfit.id))
                .limit(limit * 2).all()
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
        seasonal = attach_links(seasonal_q.order_by(desc(Outfit.created_at)).limit(limit * 2).all())

        # ── 3. Casual Collection ──────────────────────────────────────────
        casual = attach_links(
            gender_filter(Outfit.query.filter(Outfit.occasion == 'casual'))
            .order_by(Outfit.id)
            .limit(limit * 2).all()
        )

        # ── 4. Formal & Work Wear ─────────────────────────────────────────
        formal = attach_links(
            gender_filter(
                Outfit.query.filter(Outfit.occasion.in_(['formal', 'work']))
            )
            .order_by(desc(Outfit.trend_score), Outfit.id)
            .limit(limit * 2).all()
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
            .limit(limit * 2).all()
        )
        if len(sports) < 3:
            sports = attach_links(
                gender_filter(Outfit.query.filter(Outfit.occasion.in_(['casual', 'summer'])))
                .order_by(desc(Outfit.id))
                .limit(limit * 2).all()
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
            .limit(limit * 2).all()
        )

        # ── 7. Party & Date Night ─────────────────────────────────────────
        party = attach_links(
            gender_filter(
                Outfit.query.filter(Outfit.occasion.in_(['party', 'date']))
            )
            .order_by(desc(Outfit.trend_score), desc(Outfit.id))
            .limit(limit * 2).all()
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

@bp.route('/similar/<int:outfit_id>', methods=['GET'])
@jwt_required()
def get_similar(outfit_id):
    from models.outfit import Outfit
    from models.user import UserProfile, StylePreference
    from services.shopping_service import SerpApiShoppingService
    from extensions import db
    
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)
        
        main_outfit = db.session.get(Outfit, outfit_id)
        if not main_outfit:
            return jsonify({'error': 'Outfit not found'}), 404
            
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        preferences = StylePreference.query.filter_by(user_id=user_id).first()
        
        shopping_service = SerpApiShoppingService()
        compatible_colors = main_outfit.colors if main_outfit.colors else []
        occasion = main_outfit.occasion or 'casual'
        
        # Fetch live similar items from SerpApi shopping API
        outfit_dict = main_outfit.to_dict()
        similar_outfits = shopping_service.fetch_similar_live_products(outfit_dict, profile, limit=4)
        return jsonify({'similar': similar_outfits}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
