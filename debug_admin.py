# Run this in your terminal/flask shell
from app import create_app, db
from app.models.models import Category


app = create_app()
with app.app_context():
    all_cats = Category.query.all()
    print(f"Total Categories: {len(all_cats)}")
    for c in all_cats:
        print(f"Name: {c.name}, Parent ID: {c.parent_id}")