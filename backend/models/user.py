from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    preferences = db.relationship('StylePreference', backref='user', uselist=False, cascade='all, delete-orphan')
    feedbacks = db.relationship('UserFeedback', backref='user', cascade='all, delete-orphan', lazy='dynamic')
    
    def __init__(self, email=None, username=None, password_hash=None, **kwargs):
        self.email = email
        self.username = username
        if password_hash:
            self.password_hash = password_hash
        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat()
        }

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Body measurements
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    body_type = db.Column(db.String(50))  # hourglass, pear, apple, rectangle, inverted_triangle
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    
    # Additional info
    skin_tone = db.Column(db.String(50))
    profile_image = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, user_id=None, height=None, weight=None, body_type=None, age=None, gender=None, skin_tone=None, profile_image=None, **kwargs):
        self.user_id = user_id
        self.height = height
        self.weight = weight
        self.body_type = body_type
        self.age = age
        self.gender = gender
        self.skin_tone = skin_tone
        self.profile_image = profile_image
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'height': self.height,
            'weight': self.weight,
            'body_type': self.body_type,
            'age': self.age,
            'gender': self.gender,
            'skin_tone': self.skin_tone
        }

class StylePreference(db.Model):
    __tablename__ = 'style_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Style preferences
    preferred_colors = db.Column(db.JSON)  # List of colors
    preferred_styles = db.Column(db.JSON)  # casual, formal, sporty, bohemian, etc.
    avoided_patterns = db.Column(db.JSON)
    comfort_level = db.Column(db.String(20))  # high, medium, low
    
    # Occasions
    preferred_occasions = db.Column(db.JSON)  # work, party, casual, gym, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, user_id=None, preferred_colors=None, preferred_styles=None, avoided_patterns=None, comfort_level=None, preferred_occasions=None, **kwargs):
        self.user_id = user_id
        self.preferred_colors = preferred_colors
        self.preferred_styles = preferred_styles
        self.avoided_patterns = avoided_patterns
        self.comfort_level = comfort_level
        self.preferred_occasions = preferred_occasions
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferred_colors': self.preferred_colors,
            'preferred_styles': self.preferred_styles,
            'avoided_patterns': self.avoided_patterns,
            'comfort_level': self.comfort_level,
            'preferred_occasions': self.preferred_occasions
        }
