from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app.models.models import db, CartItem, ProductVariant, Product
from app.utils import login_required
from sqlalchemy.orm import joinedload
import os
import razorpay

cart = Blueprint('cart', __name__)


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@cart.route('/')
@login_required
def view_cart():
    """Display all items in the user's shopping bag."""
    items = CartItem.query.filter_by(user_id=g.current_user.id)\
        .options(joinedload(CartItem.variant).joinedload(ProductVariant.product))\
        .all()
    
    total_paise = sum(item.variant.product.price * item.quantity for item in items)
    total_amount = total_paise / 100
    
    return render_template('cart/cart.html', items=items, total=total_amount)

@cart.route('/add/<int:id>', methods=['POST'])
@login_required
def add(id):
    """Add a product variant to the cart."""
    variant_id = request.form.get('variant_id')
    quantity = int(request.form.get('quantity', 1))

    if not variant_id:
        flash("Please select a size.", "danger")
        return redirect(url_for('main.product_detail', id=id))

    variant = ProductVariant.query.get_or_404(variant_id)
    if variant.stock < quantity:
        flash(f"Only {variant.stock} pieces left in this size.", "warning")
        return redirect(url_for('main.product_detail', id=id))

    existing_item = CartItem.query.filter_by(
        user_id=g.current_user.id, 
        variant_id=variant_id
    ).first()
    
    if existing_item:
        if variant.stock < (existing_item.quantity + quantity):
            flash("Stock limit reached for this size.", "warning")
        else:
            existing_item.quantity += quantity
    else:
        new_item = CartItem(user_id=g.current_user.id, variant_id=variant_id, quantity=quantity)
        db.session.add(new_item)
    
    db.session.commit()
    flash("Piece added to your Atelier Bag.", "success")
    return redirect(url_for('cart.view_cart'))

@cart.route('/remove/<int:id>')
@login_required
def remove(id):
    """Remove an item from the cart."""
    item = CartItem.query.get_or_404(id)
    if item.user_id == g.current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from bag.", "success")
    return redirect(url_for('cart.view_cart'))

@cart.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    """Update quantity of an item already in the cart."""
    item = CartItem.query.get_or_404(id)
    new_qty = int(request.form.get('quantity'))
    
    if item.user_id == g.current_user.id and new_qty > 0:
        if item.variant.stock >= new_qty:
            item.quantity = new_qty
            db.session.commit()
        else:
            flash("Requested quantity exceeds available stock.", "danger")
            
    return redirect(url_for('cart.view_cart'))

@cart.route('/checkout')
@login_required
def checkout():
    """Step 1: Display the compulsory shipping form and bag summary."""
    items = CartItem.query.filter_by(user_id=g.current_user.id)\
        .options(joinedload(CartItem.variant).joinedload(ProductVariant.product))\
        .all()
        
    if not items:
        flash("Your bag is empty.", "warning")
        return redirect(url_for('main.home'))

    total_paise = sum(item.variant.product.price * item.quantity for item in items)
    total_amount = total_paise / 100
    
    # We pass 'user' so the form can be pre-filled with existing data
    return render_template('cart/checkout.html', 
                           items=items, 
                           total=total_amount, 
                           user=g.current_user)

@cart.route('/process-checkout', methods=['POST'])
@login_required
def process_checkout():
    # ... (Your existing address saving logic here) ...

    # Calculate amount in PAISE (₹1 = 100 paise)
    cart_items = CartItem.query.filter_by(user_id=g.current_user.id).all()
    total_paise = sum(item.variant.product.price * item.quantity for item in cart_items)

    try:
        # Create Razorpay Order
        order_data = {
            "amount": total_paise,
            "currency": "INR",
            "receipt": f"order_rcpt_{g.current_user.id}",
            "payment_capture": 1 # Auto-capture payment
        }
        razorpay_order = client.order.create(data=order_data)
        
        return render_template('cart/payment.html', 
                               order_id=razorpay_order['id'],
                               key_id=os.getenv("RAZORPAY_KEY_ID"),
                               amount=total_paise,
                               user=g.current_user)
    except Exception as e:
        flash("Payment gateway error. Please try again.", "danger")
        return redirect(url_for('cart.checkout'))
    
@cart.route('/buy-now/<int:id>', methods=['POST'])
@login_required
def buy_now(id):
    """Fast-track: Add specific item and jump straight to checkout."""
    variant_id = request.form.get('variant_id')
    quantity = int(request.form.get('quantity', 1))

    if not variant_id:
        flash("Please select a size.", "danger")
        return redirect(url_for('main.product_detail', id=id))

    # Add to cart (Update qty if exists, else create new)
    existing_item = CartItem.query.filter_by(user_id=g.current_user.id, variant_id=variant_id).first()
    if existing_item:
        existing_item.quantity = quantity
    else:
        new_item = CartItem(user_id=g.current_user.id, variant_id=variant_id, quantity=quantity)
        db.session.add(new_item)
    
    db.session.commit()
    return redirect(url_for('cart.checkout'))       

@cart.route('/verify-payment')
@login_required
def verify_payment():
    order_id = request.args.get('ord_id')
    payment_id = request.args.get('pay_id')
    signature = request.args.get('sig')

    params_dict = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
    }

    try:
        # This will raise an error if the signature is invalid
        client.utility.verify_payment_signature(params_dict)
        
        # 1. Clear the Cart
        CartItem.query.filter_by(user_id=g.current_user.id).delete()
        db.session.commit()
        
        # 2. Redirect to Success Page
        return render_template('cart/success.html', payment_id=payment_id)
        
    except Exception:
        flash("Payment verification failed. Please contact support.", "danger")
        return redirect(url_for('main.home'))
