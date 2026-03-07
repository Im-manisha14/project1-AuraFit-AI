"""
Migration: add gender support to AuraFit
- Adds `gender` column to outfits table
- Assigns gender to all existing outfits
- Inserts male-specific outfits with Unsplash images
Run once:  python migrate_gender.py
"""
from app import app
from extensions import db
from models.outfit import Outfit
import sqlite3, os

# ── Map existing outfit names → gender ───────────────────────────
OUTFIT_GENDER_MAP = {
    # female-specific
    'Athleisure Chic': 'female',
    'Elegant Evening Dress': 'female',
    'Boho Festival Look': 'female',
    'Date Night Elegance': 'female',
    'Spring Pastels': 'female',
    'Party Sequin Glam': 'female',
    'Sunset Date Dress': 'female',
    'Yoga Flow Set': 'female',
    'Office Power Blazer': 'female',
    'Winter Coat Statement': 'female',
    'Beach Resort Luxe': 'female',
    'Retro Vintage Revival': 'female',
    'Sustainable Work Chic': 'female',
    # male-specific
    'Black Tie Tuxedo': 'male',
    'Smart Casual Friday': 'male',
    'Summer Breeze': 'male',
    # unisex
    'Classic Business Suit': 'unisex',
    'Cozy Winter Layers': 'unisex',
    'Minimalist Modern': 'unisex',
    'Streetwear Urban': 'unisex',
    'Autumn Date Night': 'unisex',
}

# ── New male outfits to insert ────────────────────────────────────
MALE_OUTFITS = [
    dict(
        name='Athletic Casual Set',
        description='Fitted tee with slim-cut joggers – perfect for the athletic build',
        top='Fitted Crew-Neck Tee',
        bottom='Slim Joggers',
        shoes='Sneakers',
        gender='male',
        occasion='casual',
        season='all',
        style_type='athletic',
        colors=['white', 'black'],
        fabric_types=['cotton', 'polyester'],
        comfort_score=0.92,
        is_trending=True,
        trend_score=0.88,
        image_url='https://images.unsplash.com/photo-1617196034183-421b4040ed20?w=600&q=80',
    ),
    dict(
        name="Men's Summer Linen Shirt",
        description='Breathable linen shirt with chinos for a sharp summer look',
        top='Linen Button-Down Shirt',
        bottom='Slim Chinos',
        shoes='Loafers',
        gender='male',
        occasion='casual',
        season='summer',
        style_type='smart-casual',
        colors=['beige', 'white'],
        fabric_types=['linen', 'cotton'],
        comfort_score=0.90,
        is_trending=True,
        trend_score=0.85,
        image_url='https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=600&q=80',
    ),
    dict(
        name="Men's Office Power Suit",
        description='Structured blazer and tailored trousers for a commanding office presence',
        top='Structured Blazer & Dress Shirt',
        bottom='Tailored Trousers',
        shoes='Oxford Shoes',
        gender='male',
        occasion='work',
        season='all',
        style_type='formal',
        colors=['navy', 'white'],
        fabric_types=['wool', 'cotton'],
        comfort_score=0.72,
        is_trending=False,
        trend_score=0.70,
        image_url='https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=600&q=80',
    ),
    dict(
        name="Men's Party Night Look",
        description='Sharp printed shirt with dark jeans for a confident party entry',
        top='Slim-Fit Printed Shirt',
        bottom='Dark Skinny Jeans',
        shoes='Chelsea Boots',
        gender='male',
        occasion='party',
        season='all',
        style_type='smart-casual',
        colors=['black', 'navy'],
        fabric_types=['cotton', 'denim'],
        comfort_score=0.78,
        is_trending=True,
        trend_score=0.82,
        image_url='https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80',
    ),
    dict(
        name="Men's Smart Date Outfit",
        description='Relaxed blazer over a plain tee – smart yet approachable for a date',
        top='Relaxed Blazer & Plain Tee',
        bottom='Slim Chinos',
        shoes='Derby Shoes',
        gender='male',
        occasion='date',
        season='all',
        style_type='smart-casual',
        colors=['gray', 'white'],
        fabric_types=['wool blend', 'cotton'],
        comfort_score=0.80,
        is_trending=True,
        trend_score=0.83,
        image_url='https://images.unsplash.com/photo-1516826957135-700dedea698c?w=600&q=80',
    ),
    dict(
        name="Men's Gym Performance Set",
        description='Moisture-wicking tank and athletic shorts built for high-intensity training',
        top='Compression Tank Top',
        bottom='Athletic Shorts',
        shoes='Training Sneakers',
        gender='male',
        occasion='gym',
        season='all',
        style_type='athletic',
        colors=['black', 'electric blue'],
        fabric_types=['polyester', 'elastane'],
        comfort_score=0.96,
        is_trending=True,
        trend_score=0.90,
        image_url='https://images.unsplash.com/photo-1541216970279-affbfdd55aa8?w=600&q=80',
    ),
    dict(
        name="Men's Winter Bomber Jacket",
        description='Padded bomber jacket layered over a hoodie for a stylish winter street look',
        top='Padded Bomber Jacket & Hoodie',
        bottom='Dark Slim Jeans',
        shoes='High-Top Boots',
        gender='male',
        occasion='casual',
        season='winter',
        style_type='streetwear',
        colors=['olive', 'black'],
        fabric_types=['nylon', 'fleece', 'denim'],
        comfort_score=0.87,
        is_trending=True,
        trend_score=0.86,
        image_url='https://images.unsplash.com/photo-1520975954732-35dd22299614?w=600&q=80',
    ),
    dict(
        name="Men's Formal Dinner Suit",
        description='Classic black suit with white dress shirt for black-tie events',
        top='Black Suit Jacket & White Dress Shirt',
        bottom='Black Dress Trousers',
        shoes='Patent Leather Oxfords',
        gender='male',
        occasion='formal',
        season='all',
        style_type='formal',
        colors=['black', 'white'],
        fabric_types=['wool', 'cotton'],
        comfort_score=0.68,
        is_trending=False,
        trend_score=0.72,
        image_url='https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=600&q=80',
    ),
    dict(
        name="Men's Layered Minimalist Look",
        description='Clean layered minimalist outfit ideal for slim and average builds',
        top='Slim Turtleneck',
        bottom='Wide-Leg Trousers',
        shoes='White Sneakers',
        gender='male',
        occasion='casual',
        season='fall',
        style_type='minimalist',
        colors=['cream', 'beige'],
        fabric_types=['cotton', 'linen'],
        comfort_score=0.88,
        is_trending=True,
        trend_score=0.84,
        image_url='https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600&q=80',
    ),
    dict(
        name="Men's Streetwear Hoodie Set",
        description='Oversized hoodie with cargo pants – the go-to urban casual combo',
        top='Oversized Graphic Hoodie',
        bottom='Cargo Pants',
        shoes='Chunky Sneakers',
        gender='male',
        occasion='casual',
        season='all',
        style_type='streetwear',
        colors=['gray', 'khaki'],
        fabric_types=['cotton fleece', 'cotton twill'],
        comfort_score=0.93,
        is_trending=True,
        trend_score=0.91,
        image_url='https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=600&q=80',
    ),
]


def run_migration():
    with app.app_context():
        # ── Step 1: Add gender column if it doesn't exist ─────────
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.join(app.instance_path, db_path.lstrip('/'))

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Check if column exists
        cur.execute("PRAGMA table_info(outfits)")
        cols = [row[1] for row in cur.fetchall()]
        if 'gender' not in cols:
            cur.execute("ALTER TABLE outfits ADD COLUMN gender TEXT DEFAULT 'unisex'")
            conn.commit()
            print("✅ Added `gender` column to outfits table")
        else:
            print("ℹ️  `gender` column already exists")

        conn.close()

        # ── Step 2: Assign gender to existing outfits ─────────────
        updated = 0
        for outfit in Outfit.query.all():
            assigned = OUTFIT_GENDER_MAP.get(outfit.name)
            if assigned and outfit.gender != assigned:
                outfit.gender = assigned
                updated += 1
        db.session.commit()
        print(f"✅ Updated gender for {updated} existing outfits")

        # ── Step 3: Insert male outfits (skip duplicates by name) ──
        existing_names = {o.name for o in Outfit.query.all()}
        added = 0
        for data in MALE_OUTFITS:
            if data['name'] not in existing_names:
                db.session.add(Outfit(**data))
                added += 1
        db.session.commit()
        print(f"✅ Inserted {added} new male outfits")

        # ── Summary ────────────────────────────────────────────────
        total = Outfit.query.count()
        male_count = Outfit.query.filter_by(gender='male').count()
        female_count = Outfit.query.filter_by(gender='female').count()
        unisex_count = Outfit.query.filter_by(gender='unisex').count()
        print(f"\n📊 Outfit counts: total={total}  male={male_count}  female={female_count}  unisex={unisex_count}")
        print("✅ Migration complete!")


if __name__ == '__main__':
    run_migration()
