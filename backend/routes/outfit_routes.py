from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('outfit', __name__, url_prefix='/api/outfits')

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

@bp.route('/<int:outfit_id>', methods=['GET'])
@jwt_required()
def get_outfit(outfit_id):
    from models.outfit import Outfit
    
    try:
        outfit = Outfit.query.get(outfit_id)
        
        if not outfit:
            return jsonify({'error': 'Outfit not found'}), 404
        
        return jsonify({'outfit': outfit.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:outfit_id>/feedback', methods=['POST'])
@jwt_required()
def submit_feedback(outfit_id):
    from extensions import db
    from models.outfit import Outfit, UserFeedback
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        outfit = Outfit.query.get(outfit_id)
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
@jwt_required()
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
