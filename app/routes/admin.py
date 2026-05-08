from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app,g
from app import db
from app.models.models import User, Product, Category,Order,ProductVariant,Feedback
from app.utils import admin_required
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy.orm import joinedload

    # Create the Blueprint
admin= Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/dashboard')
@admin_required
def dashboard():
    # 1. Get the total count of all products
    total_products = Product.query.count()

    # 2. Fetch the 5 most recently added products
    # We use .order_by(Product.created_at.desc()) to put newest at the top
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    unread_feedback_count = Feedback.query.filter_by(status='Pending').count()

    # 3. Calculate simple stock alerts (Optional but useful)
    # This checks for any variants where stock is below 5
    low_stock_count = db.session.query(ProductVariant).filter(ProductVariant.stock <= 5).count()

    return render_template(
        'admin/dashboard.html', 
        total_products=total_products,
        recent_products=recent_products,
        unread_feedback_count=unread_feedback_count,
        low_stock_count=low_stock_count
    )

@admin.route('/add-product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        try:
            # 1. Capture Basic Product Data
            name = request.form.get('name')
            price = request.form.get('price')
            category_id = request.form.get('category_id')
            gender = request.form.get('gender')
            image_url = request.form.get('image_url')
            story = request.form.get('description')

            # 2. Create the Product record first
            # We convert price to Paise (Integer) for the database
            new_product = Product(
                name=name,
                price=int(float(price) * 100),
                category_id=category_id,
                gender=gender,
                image_url=image_url,
                story=story,
                sku=name.replace(" ", "-").lower()[:40], # Basic SKU auto-gen
                material="Atelier Luxury Blend",
                origin="Handcrafted"
            )
            
            db.session.add(new_product)
            # Flush so we have access to new_product.id for the variants
            db.session.flush()

            # 3. Capture Dynamic Size & Stock Lists
            sizes = request.form.getlist('sizes[]')
            stocks = request.form.getlist('stocks[]')

            # 4. Create a Variant entry for every size provided
            for size, stock in zip(sizes, stocks):
                if size.strip(): # Only add if size name is provided
                    variant = ProductVariant(
                        product_id=new_product.id,
                        size=size.strip(),
                        stock=int(stock or 0)
                    )
                    db.session.add(variant)

            db.session.commit()
            flash(f"Collection piece '{name}' successfully registered.", "success")
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Add Product Error: {str(e)}")
            flash("An error occurred while saving the product. Please check your inputs.", "danger")

    # GET request: Load categories for the dropdown
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)

@admin.route('/stock')
@admin_required
def stock_management():
    from sqlalchemy.orm import joinedload
    products = Product.query.options(joinedload(Product.variants)).order_by(Product.name).all()
    return render_template('admin/stock.html', products=products)

@admin.route('/product/<int:product_id>/manage')
@admin_required
def manage_product_stock(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('admin/manage_product.html', product=product)

@admin.route('/update-variant/<int:variant_id>', methods=['POST'])
@admin_required
def update_stock(variant_id):
    variant = ProductVariant.query.get_or_404(variant_id)
    new_stock = request.form.get('new_stock', type=int)
    if new_stock is not None:
        variant.stock = new_stock
        db.session.commit()
        flash(f"Stock updated for {variant.size}", "success")
    return redirect(url_for('admin.manage_product_stock', product_id=variant.product_id))


@admin.route('/delete-product/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # This will delete all variants and the product
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' removed from catalog.", "info")
    return redirect(url_for('admin.stock_management'))

# 5. Add a new size variant to an existing product
@admin.route('/product/<int:product_id>/add-variant', methods=['POST'])
@admin_required
def add_variant(product_id):
    size = request.form.get('size')
    stock = request.form.get('stock', type=int, default=0)

    if not size:
        flash("Size name is required.", "danger")
        return redirect(url_for('admin.manage_product_stock', product_id=product_id))

    # Check if size already exists for this product to prevent duplicates
    existing = ProductVariant.query.filter_by(product_id=product_id, size=size).first()
    if existing:
        flash(f"Size {size} already exists for this product.", "warning")
    else:
        new_variant = ProductVariant(product_id=product_id, size=size, stock=stock)
        db.session.add(new_variant)
        db.session.commit()
        flash(f"Size {size} added successfully.", "success")

    return redirect(url_for('admin.manage_product_stock', product_id=product_id))

# 6. Delete a specific size variant
@admin.route('/variant/<int:variant_id>/delete', methods=['POST'])
@admin_required
def delete_variant(variant_id):
    variant = ProductVariant.query.get_or_404(variant_id)
    product_id = variant.product_id
    
    db.session.delete(variant)
    db.session.commit()
    
    flash("Size variant deleted.", "info")
    return redirect(url_for('admin.manage_product_stock', product_id=product_id))

# View all feedback (The List View)
@admin.route('/admin/feedback')
@admin_required
def view_feedback():
    if not g.current_user.is_admin:
        abort(403)
        
    page = request.args.get('page', 1, type=int)
    # Paginate 15 items per page, newest first
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('admin/feedback_list.html', feedbacks=feedbacks)

# View a single feedback entry (The Detail View)
@admin.route('/admin/feedback/<int:feedback_id>')
@admin_required
def view_single_feedback(feedback_id):
    if not g.current_user.is_admin:
        abort(403)
        
    feedback = Feedback.query.get_or_404(feedback_id)
    
    # Mark as Read automatically when opened
    if feedback.status == 'Pending':
        feedback.status = 'Read'
        db.session.commit()
        
    return render_template('admin/feedback_detail.html', feedback=feedback)

# Permanent Archive (The Delete Action)
@admin.route('/admin/feedback/<int:feedback_id>/delete', methods=['POST'])
@admin_required
def delete_feedback(feedback_id):
    if not g.current_user.is_admin:
        abort(403)
        
    feedback = Feedback.query.get_or_404(feedback_id)
    
    try:
        db.session.delete(feedback)
        db.session.commit()
        flash("Dialogue archived permanently.", "success")
    except Exception:
        db.session.rollback()
        flash("Error archiving dialogue.", "danger")
        
    return redirect(url_for('admin.view_feedback'))