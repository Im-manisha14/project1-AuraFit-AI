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
