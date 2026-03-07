from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('user', __name__, url_prefix='/api/users')

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    from extensions import db
    from models.user import UserProfile
    
    try:
        user_id_str = get_jwt_identity()
        print(f"[USER /profile] Getting profile for user_id: {user_id_str}")
        
        if not user_id_str:
            print("[USER /profile] ERROR: No user_id from token")
            return jsonify({'error': 'Invalid token'}), 401
        
        # Convert string identity back to int
        user_id = int(user_id_str)
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            # Create default profile
            print(f"[USER /profile] Creating new profile for user_id: {user_id}")
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            db.session.commit()
        
        print(f"[USER /profile] SUCCESS: Returning profile for user_id: {user_id}")
        return jsonify({'profile': profile.to_dict()}), 200
        
    except Exception as e:
        print(f"[USER /profile] ERROR: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['POST', 'PUT'])
@jwt_required()
def update_profile():
    from extensions import db
    from models.user import UserProfile
    
    try:
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
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
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
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
        user_id_str = get_jwt_identity()
        # Convert string identity back to int
        user_id = int(user_id_str)
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


@bp.route('/body-types', methods=['GET'])
@jwt_required()
def get_body_types():
    """Return valid body type options for a given gender."""
    gender = request.args.get('gender', '').lower().strip()

    MALE_TYPES = ['athletic', 'slim', 'average', 'muscular', 'heavy']
    FEMALE_TYPES = ['hourglass', 'pear', 'apple', 'rectangle', 'inverted_triangle']

    if gender == 'male':
        body_types = MALE_TYPES
    elif gender == 'female':
        body_types = FEMALE_TYPES
    else:
        body_types = MALE_TYPES + FEMALE_TYPES

    return jsonify({'gender': gender or 'all', 'body_types': body_types}), 200
