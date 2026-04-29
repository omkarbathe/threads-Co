from app import create_app, db

app = create_app()

with app.app_context():
    print("Dropping old tables...")
    db.drop_all()
    print("Creating new eCommerce schema in RDS...")
    db.create_all()
    print("Database is ready for Admin & Payments!")