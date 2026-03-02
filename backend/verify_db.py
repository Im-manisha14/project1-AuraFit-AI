from extensions import db
from app import create_app

app = create_app()

print('=' * 60)
print('AURAFIT DATABASE STATUS')
print('=' * 60)

with app.app_context():
    # Show database URI (hide password for security)
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    safe_uri = db_uri.replace('Manisha14', '****')
    print(f'Database URI: {safe_uri}')
    
    # Test connection
    try:
        result = db.session.execute(db.text('SELECT version()'))
        version = result.fetchone()[0]
        print(f'✓ PostgreSQL Connection: SUCCESS')
        print(f'  Version: {version.split(",")[0]}')
    except Exception as e:
        print(f'✗ Connection Error: {e}')
        exit(1)
    
    # Check tables
    try:
        result = db.session.execute(db.text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        print(f'\nTables found: {len(tables)}')
        for table in tables:
            print(f'  ✓ {table}')
    except Exception as e:
        print(f'✗ Error checking tables: {e}')
    
    # Check data counts
    try:
        from models.user import User
        from models.outfit import Outfit
        
        user_count = User.query.count()
        outfit_count = Outfit.query.count()
        
        print(f'\nData Summary:')
        print(f'  Users: {user_count}')
        print(f'  Outfits: {outfit_count}')
        
    except Exception as e:
        print(f'✗ Error checking data: {e}')
    
    print('\n✅ Database verification complete!')