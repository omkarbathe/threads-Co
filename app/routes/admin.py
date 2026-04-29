from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app import db
from app.models.models import User, Product, Category,Order
from app.utils import admin_required
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func


# Create the Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
   # 1. Count products and orders
    product_count = Product.query.count()
    order_count = Order.query.count()
    
    # 2. Sum revenue from 'Paid' or 'Delivered' orders
    total_revenue = db.session.query(func.sum(Order.total_amount))\
                              .filter(Order.status.in_(['Paid', 'Delivered']))\
                              .scalar() or 0
    
    return render_template('admin/dashboard.html', 
                           product_count=product_count, 
                           order_count=order_count, 
                           total_revenue=total_revenue)



@admin_bp.route('add-product', methods=['GET', 'POST'])
@admin_required # Using your existing protection
def add_product():
    if request.method == 'POST':
        # 1. Grab the file from the request
        file = request.files.get('product_image')
        
        if file and file.filename != '':
            # Secure the filename to prevent directory traversal attacks
            filename = secure_filename(file.filename)
            
            # Define the relative path for the DB and the absolute path for saving
            relative_path = os.path.join('uploads', 'products', filename)
            absolute_path = os.path.join(current_app.root_path, 'static', relative_path)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            
            # Save the physical file
            file.save(absolute_path)
            
            # 2. Create the Product Record
            try:
                # Handle discount price safely
                d_price = request.form.get('discount_price')
                discount_price = int(d_price) if d_price and d_price.strip() else None

                new_product = Product(
                    name=request.form.get('name'),
                    description=request.form.get('description'),
                    price=int(request.form.get('price')),
                    discount_price=discount_price,
                    image_url=relative_path.replace("\\", "/"), # Standardize slashes for URLs
                    gender=request.form.get('gender'),
                    collection_tag=request.form.get('collection_tag'),
                    category_id=int(request.form.get('category_id')),
                    stock=int(request.form.get('stock', 10)),
                    is_new=True if request.form.get('is_new') else False,
                    is_featured=True if request.form.get('is_featured') else False
                )
                
                db.session.add(new_product)
                db.session.commit()
                flash(f"Product '{new_product.name}' uploaded successfully!", "success")
                return redirect(url_for('admin.manage_products'))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Database Error: {str(e)}", "danger")
        else:
            flash("Please select a valid image file.", "danger")

    main_categories = Category.query.filter_by(parent_id=None).all()
    return render_template('admin/add_product.html', categories=main_categories)

@admin_bp.route('/admin/manage-products')
@admin_required
def manage_products():
    # Fetch products and join with category to minimize database queries
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/manage_products.html', products=products) 

@admin_bp.route('/admin/delete-product/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)