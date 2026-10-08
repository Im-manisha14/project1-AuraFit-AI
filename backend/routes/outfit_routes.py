from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('outfit', __name__, url_prefix='/api/outfits')

@bp.route('/test-shopping', methods=['GET', 'POST'])
def test_shopping():
    from services.shopping_service import SerpApiShoppingService
    import os
    
    query = request.args.get('q', 'women burgundy midi dress')
    if request.method == 'POST':
        data = request.json or {}
        query = data.get('q', query)
        
    service = SerpApiShoppingService()
    if not service.is_configured():
        return jsonify({"error": "SERPAPI_KEY is not configured", "status": "FAIL"}), 400
        
    try:
        import requests
        params = {
            "engine": "google_shopping",
            "q": query,
            "gl": "in",
            "hl": "en",
            "api_key": service.api_key
        }
        resp = requests.get(service.base_url, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("shopping_results", [])
        
        parsed = []
        for r in results:
            parsed.append({
                "title": r.get("title"),
                "retailer": r.get("source"),
                "price": r.get("extracted_price"),
                "currency": r.get("currency"),
                "image_url": r.get("thumbnail"),
                "merchant_url": r.get("product_link") or r.get("link"),
                "product_id": r.get("product_id") or r.get("id"),
                "delivery": r.get("delivery")
            })
            
        return jsonify({
            "status": "PASS",
            "results_count": len(results),
            "results": parsed
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "FAIL"}), 500

@bp.route('/retailer-status', methods=['GET'])
def get_retailer_status():
    """Return status matrix for all integrated retailers."""
    from services.shopping_service import SerpApiShoppingService, MultiRetailerShoppingManager
    
    shopping_service = SerpApiShoppingService()
    manager = MultiRetailerShoppingManager()
    status_matrix = manager.get_retailer_status_matrix(serpapi_configured=shopping_service.is_configured())
    
    return jsonify({
        "status": "PASS",
        "serpapi_configured": shopping_service.is_configured(),
        "retailers": status_matrix
    }), 200

@bp.route('/', methods=['GET'])
@jwt_required()
def get_outfits():
    from models.outfit import Outfit
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filters
        occasion = request.args.get('occasion')
        season = request.args.get('season')
        style_type = request.args.get('style_type')
        
        query = Outfit.query
        
        if occasion:
            query = query.filter_by(occasion=occasion)
        if season:
            query = query.filter_by(season=season)
        if style_type:
            query = query.filter_by(style_type=style_type)
        
        outfits = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'outfits': [outfit.to_dict() for outfit in outfits.items],
            'total': outfits.total,
            'pages': outfits.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<outfit_id>', methods=['GET'])
@jwt_required()
def get_outfit(outfit_id):
    from models.outfit import Outfit
    from services.product_contract import format_recommendation_contract
    from extensions import db
    
    try:
        outfit = None
        try:
            int_id = int(outfit_id)
            outfit = db.session.get(Outfit, int_id)
        except (ValueError, TypeError):
            pass

        if not outfit:
            outfit = Outfit.query.filter_by(external_id=str(outfit_id)).first()
        if not outfit and 'sim_' in str(outfit_id):
            clean_ext = str(outfit_id).replace('serpapi_sim_', 'serpapi_')
            outfit = Outfit.query.filter_by(external_id=clean_ext).first()
        
        if not outfit:
            return jsonify({'error': 'Outfit not found'}), 404
        
        outfit_dict = outfit.to_dict()
        
        # Attach shopping links (direct exact retailer links)
        if outfit.product_url and outfit_dict.get('exact_product_link_available'):
            retailer_key = (outfit.store or outfit.brand or 'store').lower().replace(' ', '')
            outfit_dict['shopping_links'] = { retailer_key: outfit.product_url }
            outfit_dict['shopping_url'] = outfit.product_url
        else:
            outfit_dict['shopping_links'] = {}
            outfit_dict['shopping_url'] = None

        contract_outfit = format_recommendation_contract(
            item=outfit_dict,
            fallback_gender=outfit.gender or 'female',
            fallback_category=outfit.category or 'dress',
            fallback_occasion=outfit.occasion or 'casual',
            fallback_season=outfit.season or 'all_season'
        )
        
        return jsonify({
            'outfit': contract_outfit,
            **contract_outfit
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:outfit_id>/feedback', methods=['POST'])
@jwt_required()
def submit_feedback(outfit_id):
    from extensions import db
    from models.outfit import Outfit, UserFeedback
    
    try:
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
        data = request.get_json()
        
        outfit = db.session.get(Outfit, outfit_id)
        if not outfit:
            return jsonify({'error': 'Outfit not found'}), 404
        
        # Check if feedback already exists
        feedback = UserFeedback.query.filter_by(
            user_id=user_id,
            outfit_id=outfit_id
        ).first()
        
        if not feedback:
            feedback = UserFeedback(user_id=user_id, outfit_id=outfit_id)
            db.session.add(feedback)
        
        # Update feedback
        if 'rating' in data:
            feedback.rating = data['rating']
        if 'liked' in data:
            feedback.liked = data['liked']
        if 'worn' in data:
            feedback.worn = data['worn']
        if 'comfort_feedback' in data:
            feedback.comfort_feedback = data['comfort_feedback']
        if 'style_feedback' in data:
            feedback.style_feedback = data['style_feedback']
        if 'comments' in data:
            feedback.comments = data['comments']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Feedback submitted successfully',
            'feedback': feedback.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/trending', methods=['GET'])
def get_trending():
    from models.outfit import Outfit
    
    try:
        limit = request.args.get('limit', 10, type=int)
        
        outfits = Outfit.query.filter_by(is_trending=True)\
            .order_by(Outfit.trend_score.desc())\
            .limit(limit).all()
        
        return jsonify({
            'outfits': [outfit.to_dict() for outfit in outfits]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
