from app import create_app, db
from app.models.models import User

app = create_app()
with app.app_context():
    # Find the user by the email you see on the screen
    user = User.query.filter_by(email='omkarbathe555@gmail.com').first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"DONE: {user.email} is now an Admin.")
        