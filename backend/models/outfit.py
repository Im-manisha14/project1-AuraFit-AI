from extensions import db
from datetime import datetime

class Outfit(db.Model):
    __tablename__ = 'outfits'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Outfit components
    top = db.Column(db.String(100))
    bottom = db.Column(db.String(100))
    shoes = db.Column(db.String(100))
    accessories = db.Column(db.JSON)
    
    # Attributes
    gender = db.Column(db.String(20), default='unisex')  # male, female, unisex
    occasion = db.Column(db.String(50))
    season = db.Column(db.String(20))
    style_type = db.Column(db.String(50))
    colors = db.Column(db.JSON)
    
    # Fabric info
    fabric_types = db.Column(db.JSON)
    comfort_score = db.Column(db.Float)
    
    # Images
    image_url = db.Column(db.String(255))
    
    # Metadata
    is_trending = db.Column(db.Boolean, default=False)
    trend_score = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'top': self.top,
            'bottom': self.bottom,
            'shoes': self.shoes,
            'accessories': self.accessories,
            'gender': self.gender,
            'occasion': self.occasion,
            'season': self.season,
            'style_type': self.style_type,
            'colors': self.colors,
            'fabric_types': self.fabric_types,
            'comfort_score': self.comfort_score,
            'is_trending': self.is_trending,
            'trend_score': self.trend_score,
            'image_url': self.image_url
        }

class UserFeedback(db.Model):
    __tablename__ = 'user_feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.id'), nullable=False)
    
    # Feedback
    rating = db.Column(db.Integer)  # 1-5
    liked = db.Column(db.Boolean)
    worn = db.Column(db.Boolean, default=False)
    
    # Detailed feedback
    comfort_feedback = db.Column(db.Integer)  # 1-5
    style_feedback = db.Column(db.Integer)  # 1-5
    comments = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    outfit = db.relationship('Outfit', backref='feedbacks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'outfit_id': self.outfit_id,
            'rating': self.rating,
            'liked': self.liked,
            'worn': self.worn,
            'comfort_feedback': self.comfort_feedback,
            'style_feedback': self.style_feedback,
            'comments': self.comments,
            'created_at': self.created_at.isoformat()
        }

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.id'), nullable=False)
    
    # Scores
    overall_score = db.Column(db.Float)
    style_match_score = db.Column(db.Float)
    comfort_score = db.Column(db.Float)
    trend_score = db.Column(db.Float)
    body_type_score = db.Column(db.Float)
    
    # Context
    occasion = db.Column(db.String(50))
    season = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='recommendations')
    outfit = db.relationship('Outfit', backref='recommendations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'outfit_id': self.outfit_id,
            'overall_score': self.overall_score,
            'style_match_score': self.style_match_score,
            'comfort_score': self.comfort_score,
            'trend_score': self.trend_score,
            'body_type_score': self.body_type_score,
            'occasion': self.occasion,
            'season': self.season,
            'outfit': self.outfit.to_dict() if self.outfit else None
        }


class OutfitInteraction(db.Model):
    """
    Tracks every time a user views, clicks, or saves an outfit.
    Used by the collaborative filtering layer of the recommendation engine.
    """
    __tablename__ = 'outfit_interactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    outfit_id = db.Column(db.Integer, db.ForeignKey('outfits.id'), nullable=False)
    # interaction_type: 'view' | 'click' | 'save'
    interaction_type = db.Column(db.String(20), nullable=False, default='view')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='interactions')
    outfit = db.relationship('Outfit', backref='interactions')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'outfit_id': self.outfit_id,
            'interaction_type': self.interaction_type,
            'created_at': self.created_at.isoformat(),
        }
