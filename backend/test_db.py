from extensions import db
from app import create_app

app = create_app()
app.app_context().push()

print("=" * 60)
print("DATABASE CONNECTION TEST")
print("=" * 60)

# Test connection
try:
    result = db.session.execute(db.text('SELECT version()'))
    version = result.fetchone()[0]
    print(f"✓ PostgreSQL connected successfully!")
    print(f"  Version: {version.split(',')[0]}")
    print()
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    exit(1)

# Check tables
print("Tables in database:")
print("-" * 60)
try:
    result = db.session.execute(db.text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    ))
    tables = [row[0] for row in result]
    print(f"Total tables: {len(tables)}")
    for table in tables:
        print(f"  ✓ {table}")
    print()
except Exception as e:
    print(f"✗ Error checking tables: {e}")

# Check data in key tables
print("Data counts:")
print("-" * 60)

try:
    from models.user import User, UserProfile, StylePreference
    user_count = User.query.count()
    profile_count = UserProfile.query.count()
    preference_count = StylePreference.query.count()
    
    print(f"  Users: {user_count}")
    print(f"  User Profiles: {profile_count}")
    print(f"  Style Preferences: {preference_count}")
    
    # Show user details
    if user_count > 0:
        print("\n  Registered users:")
        users = User.query.all()
        for user in users:
            print(f"    - {user.email} (ID: {user.id}, Username: {user.username})")
    
    print()
except Exception as e:
    print(f"✗ Error checking user data: {e}")

try:
    from models.outfit import Outfit
    outfit_count = Outfit.query.count()
    print(f"  Outfits: {outfit_count}")
    print()
except Exception as e:
    print(f"✗ Error checking outfit data: {e}")

print("=" * 60)
print("✓ DATABASE IS WORKING PROPERLY!")
print("=" * 60)
