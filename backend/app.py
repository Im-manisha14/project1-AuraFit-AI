from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"]
    }})
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

    # Import models and create tables, then seed data
    with app.app_context():
        from models import user, outfit
        db.create_all()
        _seed_sample_outfits()

    # Register blueprints
    from routes import auth_routes, user_routes, outfit_routes, recommendation_routes, ai_routes

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(outfit_routes.bp)
    app.register_blueprint(recommendation_routes.bp)
    app.register_blueprint(ai_routes.bp)

    @app.route('/')
    def index():
        return jsonify({'message': 'Welcome to AuraFit API', 'version': '1.0.0', 'status': 'running'})

    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200

    return app


def _seed_sample_outfits():
    """Seed the database with sample outfits if the table is empty."""
    from models.outfit import Outfit

    if Outfit.query.first():
        return  # Already seeded

    print("🌱 Seeding database with sample outfits...")

    outfits = [
        # ── Casual ─────────────────────────────────────────────────
        Outfit(
            name='Minimalist Modern',
            description='Clean turtleneck paired with wide-leg trousers for an effortlessly chic everyday look.',
            top='Turtleneck Sweater', bottom='Wide-Leg Trousers', shoes='White Sneakers',
            accessories=['Minimalist Watch'], occasion='casual', season='fall',
            style_type='minimalist', colors=['beige', 'white', 'cream'],
            fabric_types=['cotton', 'linen'], comfort_score=0.88,
            is_trending=True, trend_score=0.92,
            image_url='https://images.unsplash.com/photo-1617137968427-85924c800a22?q=80&w=800'
        ),
        Outfit(
            name='Summer Breeze',
            description='Light linen shirt with relaxed shorts — perfect for warm sunny days.',
            top='Linen Shirt', bottom='Linen Shorts', shoes='Leather Sandals',
            accessories=['Straw Hat'], occasion='casual', season='summer',
            style_type='casual', colors=['white', 'beige', 'sandy tan'],
            fabric_types=['linen', 'cotton'], comfort_score=0.93,
            is_trending=True, trend_score=0.88,
            image_url='https://images.unsplash.com/photo-1523381210434-271e8be1f52b?q=80&w=800'
        ),
        Outfit(
            name='Cozy Winter Layers',
            description='A warm chunky-knit sweater over slim jeans, finished with ankle boots.',
            top='Chunky Knit Sweater', bottom='Slim Jeans', shoes='Ankle Boots',
            accessories=['Wool Scarf'], occasion='casual', season='winter',
            style_type='casual', colors=['gray', 'navy', 'cream'],
            fabric_types=['wool', 'denim'], comfort_score=0.87,
            is_trending=False, trend_score=0.68,
            image_url='https://images.unsplash.com/photo-1548036328-c9fa89d128fa?q=80&w=800'
        ),
        Outfit(
            name='Spring Pastels',
            description='Soft pastel cardigan over a floral dress — fresh and feminine for spring.',
            top='Pastel Cardigan', bottom='Floral Midi Dress', shoes='Ballet Flats',
            accessories=['Pearl Earrings'], occasion='casual', season='spring',
            style_type='feminine', colors=['lavender', 'pink', 'soft pink'],
            fabric_types=['cotton', 'rayon'], comfort_score=0.82,
            is_trending=True, trend_score=0.81,
            image_url='https://images.unsplash.com/photo-1523398002811-999ca8dec234?q=80&w=800'
        ),
        Outfit(
            name='Streetwear Urban',
            description='Bold graphic hoodie with cargo pants and classic chunky sneakers.',
            top='Graphic Hoodie', bottom='Cargo Pants', shoes='Chunky Sneakers',
            accessories=['Snapback Cap', 'Chain Necklace'], occasion='casual', season='all',
            style_type='streetwear', colors=['black', 'white', 'cobalt'],
            fabric_types=['cotton', 'nylon'], comfort_score=0.91,
            is_trending=True, trend_score=0.89,
            image_url='https://images.unsplash.com/photo-1556905055-8f358a7a47b2?q=80&w=800'
        ),
        # ── Work / Office ────────────────────────────────────────────
        Outfit(
            name='Classic Business Suit',
            description='Tailored navy blazer with matching dress trousers — timeless office authority.',
            top='Blazer', bottom='Dress Trousers', shoes='Oxford Shoes',
            accessories=['Leather Belt', 'Tie'], occasion='work', season='all',
            style_type='formal', colors=['navy', 'white'],
            fabric_types=['wool', 'cotton'], comfort_score=0.72,
            is_trending=False, trend_score=0.65,
            image_url='https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=800'
        ),
        Outfit(
            name='Smart Casual Friday',
            description='Polo shirt with chinos and loafers — relaxed yet polished for casual Fridays.',
            top='Polo Shirt', bottom='Chinos', shoes='Loafers',
            accessories=['Leather Watch'], occasion='work', season='all',
            style_type='smart-casual', colors=['navy', 'khaki', 'cream'],
            fabric_types=['cotton', 'cotton'], comfort_score=0.82,
            is_trending=False, trend_score=0.72,
            image_url='https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?q=80&w=800'
        ),
        Outfit(
            name='Office Power Blazer',
            description='Structured blazer over a silk blouse with tailored trousers — command the room.',
            top='Structured Blazer', bottom='Tailored Trousers', shoes='Block Heels',
            accessories=['Statement Necklace'], occasion='work', season='all',
            style_type='power-dressing', colors=['black', 'white', 'gold'],
            fabric_types=['polyester', 'silk'], comfort_score=0.74,
            is_trending=True, trend_score=0.83,
            image_url='https://images.unsplash.com/photo-1594938298603-c8148c4b4f35?q=80&w=800'
        ),
        Outfit(
            name='Sustainable Work Chic',
            description='Earthy-tone linen blazer and wide-leg trousers — sustainable elegance.',
            top='Linen Blazer', bottom='Wide-Leg Pants', shoes='Loafers',
            accessories=['Minimalist Watch'], occasion='work', season='spring',
            style_type='minimalist', colors=['earth tones', 'camel', 'cream'],
            fabric_types=['linen', 'linen'], comfort_score=0.86,
            is_trending=True, trend_score=0.85,
            image_url='https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=800'
        ),
        # ── Party ────────────────────────────────────────────────────
        Outfit(
            name='Elegant Evening Dress',
            description='Floor-length black silk dress with a subtle slit — effortless formal glamour.',
            top='Evening Dress (full)', bottom='N/A', shoes='Stiletto Heels',
            accessories=['Diamond Earrings', 'Clutch Bag'], occasion='party', season='all',
            style_type='formal', colors=['black'],
            fabric_types=['silk', 'satin'], comfort_score=0.62,
            is_trending=True, trend_score=0.87,
            image_url='https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=800'
        ),
        Outfit(
            name='Party Sequin Glam',
            description='Shimmering sequin mini dress that owns every dance floor.',
            top='Sequin Mini Dress (full)', bottom='N/A', shoes='Strappy Heels',
            accessories=['Evening Clutch', 'Statement Earrings'], occasion='party', season='all',
            style_type='glam', colors=['gold', 'silver'],
            fabric_types=['sequin', 'polyester'], comfort_score=0.58,
            is_trending=True, trend_score=0.91,
            image_url='https://images.unsplash.com/photo-1566139884941-d7d58c4e5da7?q=80&w=800'
        ),
        Outfit(
            name='Boho Festival Look',
            description='Flowing maxi skirt with embroidered top — free-spirited and eye-catching.',
            top='Embroidered Flowy Top', bottom='Maxi Skirt', shoes='Strappy Sandals',
            accessories=['Layered Necklaces', 'Fringe Bag'], occasion='party', season='summer',
            style_type='bohemian', colors=['terracotta', 'cream', 'gold'],
            fabric_types=['cotton', 'rayon'], comfort_score=0.84,
            is_trending=True, trend_score=0.78,
            image_url='https://images.unsplash.com/photo-1469334031218-e382a71b716b?q=80&w=800'
        ),
        # ── Date Night ───────────────────────────────────────────────
        Outfit(
            name='Date Night Elegance',
            description='Classic red blouse with a sleek pencil skirt — romantic and sophisticated.',
            top='Silk Blouse', bottom='Pencil Skirt', shoes='Pointed-Toe Heels',
            accessories=['Rose Gold Bracelet'], occasion='date', season='all',
            style_type='elegant', colors=['red', 'black'],
            fabric_types=['silk', 'polyester'], comfort_score=0.67,
            is_trending=True, trend_score=0.84,
            image_url='https://images.unsplash.com/photo-1496747611176-843222e1e57c?q=80&w=800'
        ),
        Outfit(
            name='Sunset Date Dress',
            description='A flowy floral wrap dress with block heels — effortlessly romantic.',
            top='Floral Wrap Dress (full)', bottom='N/A', shoes='Block Heels',
            accessories=['Dainty Necklace'], occasion='date', season='summer',
            style_type='feminine', colors=['coral', 'peach', 'warm brown'],
            fabric_types=['rayon', 'chiffon'], comfort_score=0.79,
            is_trending=True, trend_score=0.82,
            image_url='https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?q=80&w=800'
        ),
        Outfit(
            name='Autumn Date Night',
            description='Deep burgundy turtleneck with tailored trousers and Chelsea boots.',
            top='Ribbed Turtleneck', bottom='Tailored Trousers', shoes='Chelsea Boots',
            accessories=['Long Coat'], occasion='date', season='fall',
            style_type='elegant', colors=['maroon', 'burgundy', 'charcoal'],
            fabric_types=['wool', 'cotton'], comfort_score=0.81,
            is_trending=False, trend_score=0.73,
            image_url='https://images.unsplash.com/photo-1445205170230-053b83016050?q=80&w=800'
        ),
        # ── Gym / Sports ─────────────────────────────────────────────
        Outfit(
            name='Athleisure Chic',
            description='Stylish crop top and high-waist leggings that go from the gym straight to brunch.',
            top='Moisture-Wicking Crop Top', bottom='High-Waist Leggings', shoes='Running Sneakers',
            accessories=['Sports Watch'], occasion='gym', season='all',
            style_type='sporty', colors=['black', 'purple'],
            fabric_types=['spandex', 'polyester'], comfort_score=0.95,
            is_trending=True, trend_score=0.93,
            image_url='https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?q=80&w=800'
        ),
        Outfit(
            name='Yoga Flow Set',
            description='Breathable yoga set in calming tones — move freely, look great.',
            top='Fitted Yoga Tank', bottom='Yoga Flare Pants', shoes='Barefoot / Yoga Mat',
            accessories=['Gym Bag'], occasion='gym', season='all',
            style_type='sporty', colors=['sage green', 'cream', 'white'],
            fabric_types=['nylon', 'spandex'], comfort_score=0.97,
            is_trending=True, trend_score=0.80,
            image_url='https://images.unsplash.com/photo-1518611012118-696072aa579a?q=80&w=800'
        ),
        # ── Formal / Events ──────────────────────────────────────────
        Outfit(
            name='Black Tie Tuxedo',
            description='Classic black tuxedo with bow tie — the gold standard for formal events.',
            top='Tuxedo Jacket & Dress Shirt', bottom='Tuxedo Trousers', shoes='Patent Leather Oxfords',
            accessories=['Bow Tie', 'Cufflinks', 'Pocket Square'], occasion='formal', season='all',
            style_type='black-tie', colors=['black', 'white'],
            fabric_types=['wool', 'cotton'], comfort_score=0.68,
            is_trending=False, trend_score=0.70,
            image_url='https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?q=80&w=800'
        ),
        Outfit(
            name='Winter Coat Statement',
            description='Oversized camel wool coat over monochrome outfit — sculptural and luxurious.',
            top='Fitted Mock Neck', bottom='Straight-Leg Trousers', shoes='Knee-High Boots',
            accessories=['Camel Oversized Coat', 'Leather Gloves'], occasion='casual', season='winter',
            style_type='minimalist', colors=['camel', 'earth tones', 'cream'],
            fabric_types=['wool', 'cashmere'], comfort_score=0.83,
            is_trending=True, trend_score=0.90,
            image_url='https://images.unsplash.com/photo-1539109136881-3be0616acf4b?q=80&w=800'
        ),
        Outfit(
            name='Beach Resort Luxe',
            description='Breezy cover-up over a swimsuit with woven accessories for resort vibes.',
            top='Crochet Cover-Up', bottom='High-Waist Bikini Bottoms', shoes='Platform Sandals',
            accessories=['Woven Sun Hat', 'Raffia Bag'], occasion='casual', season='summer',
            style_type='resort', colors=['white', 'royal blue', 'gold'],
            fabric_types=['crochet', 'cotton'], comfort_score=0.90,
            is_trending=True, trend_score=0.86,
            image_url='https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=800'
        ),
        Outfit(
            name='Retro Vintage Revival',
            description='High-waist flare jeans with a tucked-in retro print blouse — vintage charm.',
            top='Retro Print Blouse', bottom='High-Waist Flare Jeans', shoes='Platform Boots',
            accessories=['Round Sunglasses', 'Belt Bag'], occasion='casual', season='spring',
            style_type='vintage', colors=['mustard', 'rust', 'terracotta'],
            fabric_types=['denim', 'cotton'], comfort_score=0.80,
            is_trending=True, trend_score=0.77,
            image_url='https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?q=80&w=800'
        ),
    ]

    for outfit in outfits:
        db.session.add(outfit)

    try:
        db.session.commit()
        print(f"✅ Seeded {len(outfits)} outfits successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Seeding failed: {e}")


# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
