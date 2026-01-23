import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
    
    # Database config (PostgreSQL) - FORCED
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Manisha14@localhost:5432/aurafit'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT config - MUST match for tokens to work
    JWT_SECRET_KEY = 'dev-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # CORS config
    CORS_HEADERS = 'Content-Type'
    
    # Upload config
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # ML Models config
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ml_models', 'trained')
