from extensions import db
from models.user import User
from app import create_app

app = create_app()

with app.app_context():
    # Check for user
    user = User.query.filter_by(email='devimanisha1411@gmail.com').first()
    
    if user:
        print(f"✓ User found!")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  ID: {user.id}")
        
        # Test password
        test_password = "test123"
        if user.check_password(test_password):
            print(f"  Password 'test123' is CORRECT")
        else:
            print(f"  Password 'test123' is INCORRECT")
    else:
        print(f"✗ No user found with email: devimanisha1411@gmail.com")
        
    # List all users
    all_users = User.query.all()
    print(f"\nTotal users in database: {len(all_users)}")
    for u in all_users:
        print(f"  - {u.email} ({u.username})")
