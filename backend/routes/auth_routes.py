from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    from extensions import db
    from models.user import User
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('email') or not data.get('password') or not data.get('username'):
            return jsonify({'error': 'Missing required fields: email, username, and password are required'}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'This email is already registered. Please use a different email or try logging in.'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'This username is already taken. Please choose a different username.'}), 400
        
        # Create new user
        user = User(
            email=data['email'],
            username=data['username']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens - JWT requires string identity
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    from extensions import db
    from models.user import User
    
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing email or password'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # JWT requires string identity
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        print(f"[AUTH login] User {user.email} logged in successfully")
        print(f"[AUTH login] Generated tokens for user_id: {user.id}")
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        print(f"[AUTH login] ERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()  # Already a string from JWT
    access_token = create_access_token(identity=identity)  # Keep as string
    return jsonify({'access_token': access_token}), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    from models.user import User
    
    try:
        user_id = get_jwt_identity()
        print(f"[AUTH /me] Got user_id from token: {user_id}")
        
        if not user_id:
            print("[AUTH /me] ERROR: No user_id in token")
            return jsonify({'error': 'Invalid token'}), 401
        
        # Convert string identity back to int for database query
        user = User.query.get(int(user_id))
        
        if not user:
            print(f"[AUTH /me] ERROR: User {user_id} not found in database")
            return jsonify({'error': 'User not found'}), 404
        
        print(f"[AUTH /me] SUCCESS: Returning user {user.email}")
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        print(f"[AUTH /me] EXCEPTION: {str(e)}")
        return jsonify({'error': str(e)}), 500
