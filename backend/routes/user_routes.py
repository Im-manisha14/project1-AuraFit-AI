from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('user', __name__, url_prefix='/api/users')

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    from extensions import db
    from models.user import UserProfile
    
    try:
        user_id = get_jwt_identity()
        print(f"[PROFILE] Getting profile for user_id: {user_id}")
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            # Create default profile
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            db.session.commit()
        
        return jsonify({'profile': profile.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['POST', 'PUT'])
@jwt_required()
def update_profile():
    from extensions import db
    from models.user import UserProfile
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
        
        # Update fields
        if 'height' in data:
            profile.height = data['height']
        if 'weight' in data:
            profile.weight = data['weight']
        if 'body_type' in data:
            profile.body_type = data['body_type']
        if 'age' in data:
            profile.age = data['age']
        if 'gender' in data:
            profile.gender = data['gender']
        if 'skin_tone' in data:
            profile.skin_tone = data['skin_tone']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': profile.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    from extensions import db
    from models.user import StylePreference
    
    try:
        user_id = get_jwt_identity()
        preferences = StylePreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            # Create default preferences
            preferences = StylePreference(
                user_id=user_id,
                preferred_colors=[],
                preferred_styles=[],
                avoided_patterns=[],
                comfort_level='medium',
                preferred_occasions=[]
            )
            db.session.add(preferences)
            db.session.commit()
        
        return jsonify({'preferences': preferences.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/preferences', methods=['POST', 'PUT'])
@jwt_required()
def update_preferences():
    from extensions import db
    from models.user import StylePreference
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        preferences = StylePreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = StylePreference(user_id=user_id)
            db.session.add(preferences)
        
        # Update fields
        if 'preferred_colors' in data:
            preferences.preferred_colors = data['preferred_colors']
        if 'preferred_styles' in data:
            preferences.preferred_styles = data['preferred_styles']
        if 'avoided_patterns' in data:
            preferences.avoided_patterns = data['avoided_patterns']
        if 'comfort_level' in data:
            preferences.comfort_level = data['comfort_level']
        if 'preferred_occasions' in data:
            preferences.preferred_occasions = data['preferred_occasions']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': preferences.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
