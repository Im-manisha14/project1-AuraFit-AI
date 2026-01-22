from extensions import db
from models.user import User
from app import create_app

app = create_app()

with app.app_context():
    # Check if user exists
    existing_user = User.query.filter_by(email='devimanisha1411@gmail.com').first()
    
    if existing_user:
        print(f"✓ User already exists!")
        print(f"  Email: {existing_user.email}")
        print(f"  Username: {existing_user.username}")
        
        # Update password to test123
        existing_user.set_password('test123')
        db.session.commit()
        print(f"  Password updated to 'test123'")
    else:
        # Create new user
        user = User(
            email='devimanisha1411@gmail.com',
            username='devimanisha'
        )
        user.set_password('test123')
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✓ User created successfully!")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Password: test123")
        print(f"  ID: {user.id}")
