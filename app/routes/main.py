from flask import Blueprint, render_template,request, flash, redirect, url_for,session
from app.models.models import Product, Category,User
from app.utils import login_required
from app import db



bp = Blueprint('main', __name__)


@bp.route('/new-arrivals')
def new_arrivals():
    # OLD WAY: Product.query.filter_by(category_id=3).all()
    # NEW WAY: Look for the True/False checkbox instead of the Category ID
    products = Product.query.filter_by(is_new=True).all()
    
    return render_template('shop/category.html', products=products, title="New Arrivals")

@bp.route('/men')
def men_collection():
    category = Category.query.filter_by(name='Men').first()
    products = Product.query.filter_by(category_id=category.id).all() if category else []
    return render_template('shop/category.html', title="Men's Collection", products=products)

@bp.route('/women')
def women_collection():
    return render_template('shop/category.html', title="Women's Collection")

@bp.route('/sale')
def sale():
    return render_template('shop/category.html', title="Flash Sale")

@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.first_name = request.form.get('first_name').strip()
        user.last_name = request.form.get('last_name').strip()
        user.phone = request.form.get('phone').strip()
        user.address = request.form.get('address').strip()
        
        db.session.commit()
        
        # Sync session name for the header
        session['user_name'] = f"{user.first_name} {user.last_name}"
        
        flash("Profile updated successfully.", "success")
        return redirect(url_for('main.profile'))

    return render_template('profile.html', user=user)


@bp.route('/')
def home():
    # 1. Get products for the Hero Slider (e.g., tagged as 'Oversized')
    hero_products = Product.query.filter_by(collection_tag='Oversized').limit(4).all()
    
    # 2. Get featured products for the "Steal" section
    steal_deals = Product.query.filter(Product.discount_price < Product.price).limit(8).all()
    
    # 3. Get main categories for the catalog (where parent_id is NULL)
    main_categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('shop/home.html', 
                           hero_products=hero_products, 
                           steal_deals=steal_deals,
                           categories=main_categories)