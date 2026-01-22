from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from extensions import db

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    CORS(app)
    db.init_app(app)
    jwt = JWTManager(app)
    
    # JWT error handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({'error': 'Invalid token', 'message': error_string}), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        return jsonify({'error': 'Missing authorization token', 'message': error_string}), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({'error': 'Token has expired', 'message': 'Please login again'}), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_data):
        return jsonify({'error': 'Token has been revoked', 'message': 'Please login again'}), 401
    
    # Import models to register them with SQLAlchemy
    with app.app_context():
        from models import user, outfit
    
    # Import and register blueprints
    from routes import auth_routes, user_routes, outfit_routes, recommendation_routes
    
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(outfit_routes.bp)
    app.register_blueprint(recommendation_routes.bp)
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Welcome to AuraFit API',
            'version': '1.0.0',
            'status': 'running'
        })

    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
