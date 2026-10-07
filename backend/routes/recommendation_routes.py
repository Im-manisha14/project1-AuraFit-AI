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
        from services.shopping_service import ProductValidator
        from services.product_contract import build_response_meta, validate_product_schema

        raw_gender = data.get('gender') or (profile.gender if profile else '')
        norm_gender = ProductValidator.normalize_gender(raw_gender)
        if norm_gender not in ('female', 'male'):
            norm_gender = 'female'

        category = (data.get('category') or ('dress' if norm_gender == 'female' else 'clothing')).strip().lower()

        # Reject invalid gender / category combinations instead of silently changing them (Section 1 Contract)
        if norm_gender == 'male' and category in ('dress', 'dresses', 'skirt', 'saree', 'lehenga', 'gown'):
            return jsonify({'error': f"Invalid category '{category}' for gender 'male'"}), 400
        if norm_gender == 'female' and category in ('menswear', 'men_clothing', 'sherwani', 'men_suit'):
            return jsonify({'error': f"Invalid category '{category}' for gender 'female'"}), 400

        occasion = (data.get('occasion') or 'casual').strip().lower()
        season = (data.get('season') or 'all').strip().lower()
        limit = max(1, min(50, int(data.get('limit') or data.get('results') or 25)))
        min_price = data.get('price_min') if data.get('price_min') is not None else data.get('min_price')
        max_price = data.get('price_max') if data.get('price_max') is not None else data.get('max_price')
        price_range = data.get('price_range')
        retailer = data.get('retailer')
        skin_tone = (data.get('skin_tone') or (profile.skin_tone if profile else 'medium')).strip().lower()

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
            retailer=retailer,
            gender=norm_gender,
            category=category
        )
        similar = getattr(engine, 'last_similar_recommendations', [])
        stats = getattr(engine, 'last_stats', {})

        # Phase 2: Authoritative validation immediately before API response
        from services.product_validator import validate_live_product
        validated_recs = []
        gen_seen_ids = set()
        gen_seen_urls = set()
        gen_seen_imgs = set()
        gen_occ_reg = {}

        for r in recommendations:
            v_res = validate_live_product(
                candidate=r,
                profile=profile,
                requested_gender=norm_gender,
                requested_category=category,
                requested_occasion=occasion,
                requested_season=season,
                price_min=min_price,
                price_max=max_price,
                price_range=price_range,
                retailer=retailer,
                seen_identity_keys=gen_seen_ids,
                seen_urls=gen_seen_urls,
                seen_images=gen_seen_imgs,
                occasion_registry=gen_occ_reg
            )
            if v_res['accepted']:
                validated_recs.append(v_res['normalized_product'])

        validated_sim = []
        for s in similar:
            v_res = validate_live_product(
                candidate=s,
                profile=profile,
                requested_gender=norm_gender,
                requested_category=category,
                requested_occasion=occasion,
                requested_season=season,
                price_min=min_price,
                price_max=max_price,
                price_range=price_range,
                retailer=retailer,
                seen_identity_keys=gen_seen_ids,
                seen_urls=gen_seen_urls,
                seen_images=gen_seen_imgs,
                occasion_registry=gen_occ_reg
            )
            if v_res['accepted']:
                validated_sim.append(v_res['normalized_product'])

        def _safe_print_line(msg):
            try:
                print(str(msg).encode('ascii', errors='replace').decode('ascii'))
            except Exception:
                pass

        _safe_print_line(f"\n[RECOMMENDATION DEBUG]")
        _safe_print_line(f"Requested:")
        _safe_print_line(f"  gender={norm_gender}")
        _safe_print_line(f"  occasion={occasion}")
        _safe_print_line(f"  season={season}")
        _safe_print_line(f"  price_range={price_range or (f'INR {min_price}-{max_price}' if (min_price or max_price) else 'all')}")
        _safe_print_line(f"  skin_tone={skin_tone}")
        _safe_print_line(f"Candidates fetched: {stats.get('candidates', len(recommendations))}")
        _safe_print_line(f"Rejected:")
        _safe_print_line(f"  gender = {stats.get('gender_rejected', 0)}")
        _safe_print_line(f"  category = {stats.get('category_rejected', 0)}")
        _safe_print_line(f"  occasion = {stats.get('occasion_rejected', 0)}")
        _safe_print_line(f"  season = {stats.get('season_rejected', 0)}")
        _safe_print_line(f"  price = {stats.get('price_rejected', 0)}")
        _safe_print_line(f"  duplicate = {stats.get('duplicates_removed', 0)}")
        _safe_print_line(f"  broken_image = {stats.get('image_rejected', 0)}")
        _safe_print_line(f"  missing_url = {stats.get('url_rejected', 0)}")
        _safe_print_line(f"  invalid_product_identity = 0")
        _safe_print_line(f"Accepted: {len(validated_recs)}")
        _safe_print_line(f"Final: {len(validated_recs)}")

        for rec in validated_recs:
            _safe_print_line(f"\n[ACCEPTED PRODUCT]")
            _safe_print_line(f"  title={rec.get('title')}")
            _safe_print_line(f"  gender={rec.get('gender')}")
            _safe_print_line(f"  category={rec.get('category')}")
            _safe_print_line(f"  primary_occasion={rec.get('primary_occasion')}")
            _safe_print_line(f"  requested_occasion={occasion}")
            _safe_print_line(f"  season={rec.get('season')}")
            _safe_print_line(f"  price={rec.get('price')}")
            _safe_print_line(f"  retailer={rec.get('retailer')}")
            _safe_print_line(f"  product_url={rec.get('product_url')}")
            _safe_print_line(f"  image_url={rec.get('image_url')}")
            _safe_print_line(f"  identity_key={rec.get('product_identity_key')}")


        meta = build_response_meta(
            gender=norm_gender,
            occasion=occasion,
            season=season,
            category=category,
            skin_tone=skin_tone,
            price_min=min_price,
            price_max=max_price,
            requested_count=limit,
            recommendations=validated_recs,
            filter_stats=stats,
            is_live=True
        )

        return jsonify({
            'recommendations': validated_recs,
            'similar_recommendations': validated_sim,
            'meta': meta
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
    Each collection uses OccasionClassifier for post-retrieval validation so the
    same dress cannot appear in both the party AND casual sections.

    Query params:
      season  – 'summer'|'winter'|'spring'|'fall'|'all'  (default 'all')
      limit   – per-collection cap, default 12
    """
    from models.outfit import Outfit, OutfitInteraction
    from models.user import UserProfile
    from services.recommendation_engine import RecommendationEngine
    from services.occasion_classifier import OccasionClassifier, SeasonClassifier
    from services.product_validator import validate_live_product
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
        global_occasion_registry = {}

        def attach_links(outfits, max_items=limit, required_occasion=None):
            """
            Phase 14 & Phase 2: Collections must use the single authoritative production validator.
            Validates live product authenticity, gender, category, occasion exclusivity,
            season, broken image rejection, and cross-occasion duplicate protection.
            """
            result = []
            for o in outfits:
                val_res = validate_live_product(
                    candidate=o,
                    profile=profile,
                    requested_gender=gender,
                    requested_category='dress' if gender == 'female' else 'clothing',
                    requested_occasion=required_occasion,
                    requested_season=season,
                    seen_identity_keys=seen_global_col_ids,
                    seen_urls=seen_global_col_urls,
                    seen_images=seen_global_col_imgs,
                    occasion_registry=global_occasion_registry
                )
                if val_res['accepted']:
                    norm_p = val_res['normalized_product']
                    norm_p['shopping_links'] = engine._generate_shopping_links(o, gender)
                    result.append(norm_p)
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
        trending = attach_links(trending_q.limit(limit * 3).all(), required_occasion='trending')
        if len(trending) < 4:
            trending = attach_links(
                gender_filter(Outfit.query)
                .order_by(desc(Outfit.trend_score), desc(Outfit.id))
                .limit(limit * 3).all(),
                required_occasion='trending'
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
        seasonal = attach_links(
            seasonal_q.order_by(desc(Outfit.created_at)).limit(limit * 3).all(),
            required_occasion='seasonal'
        )

        # ── 3. Casual Collection ──────────────────────────────────────────
        # Fetch broader set then filter by occasion classifier
        casual = attach_links(
            gender_filter(
                Outfit.query.filter(Outfit.occasion.in_(['casual', 'all']))
            ).order_by(Outfit.id).limit(limit * 4).all(),
            required_occasion='casual'
        )
        if len(casual) < 4:
            casual = attach_links(
                gender_filter(Outfit.query).order_by(Outfit.id).limit(limit * 4).all(),
                required_occasion='casual'
            )

        # ── 4. Formal & Work Wear ─────────────────────────────────────────
        formal = attach_links(
            gender_filter(
                Outfit.query.filter(Outfit.occasion.in_(['formal', 'work', 'office']))
            )
            .order_by(desc(Outfit.trend_score), Outfit.id)
            .limit(limit * 4).all(),
            required_occasion='formal'
        )
        if len(formal) < 3:
            # Try office occasion as well
            formal = attach_links(
                gender_filter(Outfit.query).order_by(desc(Outfit.id)).limit(limit * 4).all(),
                required_occasion='office'
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
            .limit(limit * 3).all(),
            required_occasion='sports'
        )
        if len(sports) < 3:
            sports = attach_links(
                gender_filter(Outfit.query.filter(Outfit.occasion.in_(['casual', 'gym'])))
                .order_by(desc(Outfit.id))
                .limit(limit * 3).all(),
                required_occasion='sports'
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
            .limit(limit * 3).all(),
            required_occasion='minimalist'
        )

        # ── 7. Party & Date Night ─────────────────────────────────────────
        # Fetch party + date DB records AND use OccasionClassifier to only keep genuine party/date
        party = attach_links(
            gender_filter(
                Outfit.query.filter(Outfit.occasion.in_(['party', 'date', 'cocktail', 'evening']))
            )
            .order_by(desc(Outfit.trend_score), desc(Outfit.id))
            .limit(limit * 4).all(),
            required_occasion='party'
        )
        if len(party) < 3:
            # Relax to any occasion but still filter by classifier
            party = attach_links(
                gender_filter(Outfit.query).order_by(desc(Outfit.id)).limit(limit * 4).all(),
                required_occasion='party'
            )

        # ── 8. Based on Skin Tone ─────────────────────────────────────────
        skin_tone_outfits = []
        if profile and profile.skin_tone:
            from services.recommendation_engine import SKIN_TONE_COMPATIBLE_COLORS
            compatible_colors = SKIN_TONE_COMPATIBLE_COLORS.get(
                profile.skin_tone.lower(), []
            )
            if compatible_colors:
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
                random.shuffle(matched)
                skin_tone_outfits = attach_links(matched[:limit * 2], required_occasion='skin_tone')

        # ── 9. For Your Body Shape ────────────────────────────────────────
        body_shape_outfits = []
        if profile and profile.body_type:
            body_type = profile.body_type.lower()
            all_outfits = gender_filter(Outfit.query).order_by(Outfit.occasion, desc(Outfit.id)).all()
            matched = []
            for o in all_outfits:
                if not o.body_type_compatibility:
                    continue
                compat = [bt.lower() for bt in o.body_type_compatibility]
                if 'all' in compat or body_type in compat:
                    matched.append(o)
            body_shape_outfits = attach_links(matched[:limit * 2], required_occasion='body_shape')

        collections_dict = {
            'trending':   { 'title': 'Trending Now', 'count': len(trending), 'items': trending },
            'seasonal':   { 'title': 'Seasonal Picks', 'count': len(seasonal), 'items': seasonal },
            'casual':     { 'title': 'Casual Style', 'count': len(casual), 'items': casual },
            'formal':     { 'title': 'Work & Formal', 'count': len(formal), 'items': formal },
            'sports':     { 'title': 'Sports & Athleisure', 'count': len(sports), 'items': sports },
            'minimalist': { 'title': 'Minimalist Fashion', 'count': len(minimalist), 'items': minimalist },
            'party':      { 'title': 'Party & Evening', 'count': len(party), 'items': party },
            'skin_tone':  { 'title': 'For Your Skin Tone', 'count': len(skin_tone_outfits), 'items': skin_tone_outfits },
            'body_shape': { 'title': 'For Your Body Shape', 'count': len(body_shape_outfits), 'items': body_shape_outfits }
        }

        return jsonify({
            'collections': collections_dict,
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
