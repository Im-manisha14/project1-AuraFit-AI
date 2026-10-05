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
            retailer=retailer
        )
        similar = getattr(engine, 'last_similar_recommendations', [])
        stats = getattr(engine, 'last_stats', {})

        meta = build_response_meta(
            gender=norm_gender,
            occasion=occasion,
            season=season,
            category=category,
            skin_tone=skin_tone,
            price_min=min_price,
            price_max=max_price,
            requested_count=limit,
            recommendations=recommendations,
            filter_stats=stats,
            is_live=True
        )

        return jsonify({
            'recommendations': recommendations,
            'similar_recommendations': similar,
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

        def attach_links(outfits, max_items=limit, required_occasion=None):
            """
            Attach shopping links, validate gender/category, deduplicate globally,
            and optionally post-classify products for a specific occasion.

            When required_occasion is set, only products that ACCEPT or SECONDARY-match
            that occasion via OccasionClassifier will be included.
            """
            result = []
            for o in outfits:
                # 1. Product & category validation
                prod_dict = {
                    'title': o.name,
                    'description': o.description or '',
                    'category': o.category or '',
                    'snippet': o.description or '',
                    'brand': o.brand or '',
                    'source': o.store or '',
                    'product_url': o.product_url or '',
                }
                if gender == 'female':
                    is_dress, _, _ = ProductValidator.is_actual_dress(prod_dict)
                    if not is_dress:
                        continue
                is_compat, _, _ = ProductValidator.is_gender_compatible(prod_dict, gender)
                if not is_compat:
                    continue

                # 2. Occasion classification guard (Section 3, 23)
                if required_occasion and required_occasion not in ('all', 'trending', 'seasonal', 'skin_tone', 'body_shape', 'minimalist'):
                    occ_result = OccasionClassifier.classify(prod_dict, required_occasion, debug=False)
                    if occ_result.decision == 'REJECT':
                        continue  # Hard reject — wrong occasion

                # 3. Image validation & global cross-collection deduplication
                img = (o.image_url or '').strip()
                if not img or '1V2w3X4y5' in img or 'dummy' in img or 'placeholder' in img:
                    continue
                tbn_m = re.search(r'q=tbn:([^&]+)', img)
                img_k = tbn_m.group(1) if tbn_m else img.split('?')[0].strip()
                if img_k in seen_global_col_imgs:
                    continue

                # 4. Canonical URL & ID deduplication
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

                from services.product_contract import format_recommendation_contract
                d = o.to_dict()
                d['shopping_links'] = engine._generate_shopping_links(o, gender)
                if o.product_url:
                    d['exact_product_link_available'] = True
                    d['shopping_url'] = canon_u or o.product_url
                else:
                    d['shopping_url'] = None

                contract_item = format_recommendation_contract(
                    item=d,
                    fallback_gender=gender,
                    fallback_category='dress' if gender == 'female' else 'clothing',
                    fallback_occasion=required_occasion or o.occasion or 'casual',
                    fallback_season=season
                )
                result.append(contract_item)
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
