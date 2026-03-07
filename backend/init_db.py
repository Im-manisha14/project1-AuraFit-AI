"""
Initialize SQLite database with schema and sample data
Run this script to set up the database for the first time
"""
from app import app
from extensions import db
from models.user import User, UserProfile, StylePreference
from models.outfit import Outfit, UserFeedback, Recommendation, OutfitInteraction

def init_db():
    """Initialize database and create all tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Add sample outfits
        add_sample_data()
        
        print("✅ Database initialized with sample data!")
        print(f"📁 Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")

def add_sample_data():
    """Add sample outfit data"""
    # Check if data already exists
    if Outfit.query.first():
        print("ℹ️  Sample data already exists, skipping...")
        return
    
    sample_outfits = [
        Outfit(
            name='Classic Business Suit',
            description='Professional navy suit perfect for business meetings',
            top='Blazer',
            bottom='Dress Pants',
            shoes='Oxford Shoes',
            occasion='work',
            season='all',
            style_type='formal',
            colors=['navy', 'white'],
            fabric_types=['wool', 'cotton'],
            comfort_score=0.7,
            is_trending=False,
            trend_score=0.6
        ),
        Outfit(
            name='Summer Breeze Outfit',
            description='Light and airy summer casual wear',
            top='Linen Shirt',
            bottom='Shorts',
            shoes='Sandals',
            occasion='casual',
            season='summer',
            style_type='casual',
            colors=['white', 'beige'],
            fabric_types=['linen', 'cotton'],
            comfort_score=0.9,
            is_trending=True,
            trend_score=0.85
        ),
        Outfit(
            name='Athleisure Chic',
            description='Trendy athletic-inspired casual wear',
            top='Crop Top',
            bottom='Leggings',
            shoes='Sneakers',
            occasion='gym',
            season='all',
            style_type='sporty',
            colors=['black', 'purple'],
            fabric_types=['spandex', 'polyester'],
            comfort_score=0.95,
            is_trending=True,
            trend_score=0.92
        ),
        Outfit(
            name='Elegant Evening Dress',
            description='Sophisticated black dress for formal events',
            top='Evening Dress',
            bottom='N/A',
            shoes='Heels',
            occasion='party',
            season='all',
            style_type='formal',
            colors=['black'],
            fabric_types=['silk', 'satin'],
            comfort_score=0.6,
            is_trending=True,
            trend_score=0.8
        ),
        Outfit(
            name='Cozy Winter Layers',
            description='Warm and stylish winter outfit',
            top='Sweater',
            bottom='Jeans',
            shoes='Boots',
            occasion='casual',
            season='winter',
            style_type='casual',
            colors=['gray', 'navy'],
            fabric_types=['wool', 'denim'],
            comfort_score=0.85,
            is_trending=False,
            trend_score=0.65
        ),
        Outfit(
            name='Boho Festival Look',
            description='Free-spirited bohemian style',
            top='Flowy Top',
            bottom='Maxi Skirt',
            shoes='Sandals',
            occasion='party',
            season='summer',
            style_type='bohemian',
            colors=['terracotta', 'cream'],
            fabric_types=['cotton', 'rayon'],
            comfort_score=0.8,
            is_trending=True,
            trend_score=0.75
        ),
        Outfit(
            name='Smart Casual Friday',
            description='Perfect balance of professional and relaxed',
            top='Polo Shirt',
            bottom='Chinos',
            shoes='Loafers',
            occasion='work',
            season='all',
            style_type='smart-casual',
            colors=['navy', 'khaki'],
            fabric_types=['cotton', 'cotton'],
            comfort_score=0.8,
            is_trending=False,
            trend_score=0.7
        ),
        Outfit(
            name='Date Night Elegance',
            description='Romantic and sophisticated outfit',
            top='Blouse',
            bottom='Pencil Skirt',
            shoes='Heels',
            occasion='date',
            season='all',
            style_type='elegant',
            colors=['red', 'black'],
            fabric_types=['silk', 'polyester'],
            comfort_score=0.65,
            is_trending=True,
            trend_score=0.82
        ),
        Outfit(
            name='Minimalist Modern',
            description='Clean lines and neutral tones',
            top='Turtleneck',
            bottom='Wide Pants',
            shoes='Sneakers',
            occasion='casual',
            season='fall',
            style_type='minimalist',
            colors=['beige', 'white'],
            fabric_types=['cotton', 'linen'],
            comfort_score=0.88,
            is_trending=True,
            trend_score=0.88
        ),
        Outfit(
            name='Spring Pastels',
            description='Soft and refreshing spring colors',
            top='Cardigan',
            bottom='Dress',
            shoes='Flats',
            occasion='casual',
            season='spring',
            style_type='feminine',
            colors=['lavender', 'pink'],
            fabric_types=['cotton', 'rayon'],
            comfort_score=0.82,
            is_trending=True,
            trend_score=0.79
        )
    ]
    
    for outfit in sample_outfits:
        db.session.add(outfit)
    
    db.session.commit()
    print(f"✅ Added {len(sample_outfits)} sample outfits!")

if __name__ == '__main__':
    init_db()
