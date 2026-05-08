from flask import Blueprint, render_template, request, session, redirect, url_for, flash, g
from app.models.models import Product, Category, User,Feedback
from app import db
from app.utils import login_required

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    categories = Category.query.all()
    cat_id = request.args.get('category_id', type=int)
    sort_option = request.args.get('sort', 'newest')
    # Capture the gender from the URL (e.g., ?gender=men)
    gender_filter = request.args.get('gender')

    query = Product.query

    # Apply Gender Filter if it exists in the URL
    if gender_filter:
        # This ensures that if gender is 'men', only products with gender 'men' are shown
        query = query.filter(Product.gender == gender_filter)

    if cat_id:
        query = query.filter_by(category_id=cat_id)

    if sort_option == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_option == 'price_high':
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.all()
    
    return render_template('main/home.html', 
                           products=products, 
                           categories=categories, 
                           current_sort=sort_option,
                           current_gender=gender_filter)

@main.route('/shop/<gender>')
def gender_shop(gender):
    categories = Category.query.all()
    products = Product.query.filter_by(gender=gender).all()
    return render_template('main/home.html', products=products, categories=categories, title=gender.title())

@main.route('/vernissage')
def new_arrivals():
    categories = Category.query.all()
    products = Product.query.order_by(Product.created_at.desc()).limit(12).all()
    return render_template('main/home.html', products=products, categories=categories, title="New Arrivals")

@main.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    paragraphs = product.story.split('\n') if product.story else []
    return render_template('main/product_detail.html', product=product, paragraphs=paragraphs)

@main.route('/profile')
def profile():
    if not g.current_user:
        return redirect(url_for('auth.login'))
    return render_template('main/profile.html', user=g.current_user)

@main.route('/size-guide')
def size_guide():
    return render_template('main/size_guide.html')

@main.route('/privacy')
def privacy():
    return render_template('main/privacy.html')

@main.route('/terms')
def terms():
    return render_template('main/terms.html')

@main.route('/about')
def about():
    return render_template('main/about.html')

@main.route('/feedback', methods=['GET', 'POST'])
@login_required  # This ensures the user must be logged in
def feedback():
    if request.method == 'POST':
        # Since they are logged in, we pull identity from g.current_user
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        new_feedback = Feedback(
            user_id=g.current_user.id,
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        try:
            db.session.add(new_feedback)
            db.session.commit()
            flash('Your message has been transmitted to the atelier.', 'success')
            return redirect(url_for('main.home'))
        except Exception:
            db.session.rollback()
            flash('Error transmitting message. Please try again.', 'danger')
            
    return render_template('main/feedback.html')