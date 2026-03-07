import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (override any inherited env vars)
load_dotenv(override=True)

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'aurafit-secret-key-2026'
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # Database config - SQLite (no external DB server required)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'aurafit.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT config
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'aurafit-jwt-secret-2026'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # CORS config
    CORS_HEADERS = 'Content-Type'

    # Upload config
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # ML Models config
    MODEL_PATH = os.path.join(basedir, 'ml_models', 'trained')
