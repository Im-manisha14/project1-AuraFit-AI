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
    
    # Import and register blueprints
    from routes import auth_routes, user_routes, outfit_routes, recommendation_routes
    
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(outfit_routes.bp)
    app.register_blueprint(recommendation_routes.bp)
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Welcome to StyleSync API',
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
