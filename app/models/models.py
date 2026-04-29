from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(100), primary_key=True) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # Split name for better UX
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    
    # eCommerce Profile Details
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    
    # The Gatekeeper Flag
    is_onboarded = db.Column(db.Boolean, default=False)
    
    # Permissions & Metadata
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='customer', lazy=True)

    @property
    def display_name(self):
        """Returns First Last, or just First, or Email prefix if nothing else exists."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.email.split('@')[0].title()

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Self-referencing link: a subcategory has a parent_id
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # Relationship to get subcategories from a parent: main_cat.subcategories
    # Relationship to get parent from a subcategory: sub_cat.parent
    subcategories = db.relationship('Category', 
                                    backref=db.backref('parent', remote_side=[id]), 
                                    lazy='dynamic')
    

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Pricing (Stored as Integers for INR)
    price = db.Column(db.Integer, nullable=False)
    discount_price = db.Column(db.Integer, nullable=True)
    
    # Targeting & Slider Logic
    gender = db.Column(db.String(20), nullable=False, default='Unisex') # 'Men', 'Women', 'Unisex'
    collection_tag = db.Column(db.String(50), nullable=True)           # 'Oversized', 'Luxe', 'New Drop'
    
    # Visuals & Inventory
    image_url = db.Column(db.String(500), nullable=False)
    is_new = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    stock = db.Column(db.Integer, default=10)
    
    # Relationship: Link to the most specific category (the subcategory)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def discount_percentage(self):
        """Calculates the % off if a discount price exists."""
        if self.discount_price and self.price > 0:
            return round(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    
    # Razorpay Integration
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    razorpay_signature = db.Column(db.String(255), nullable=True)
    
    # Status: Pending, Paid, Shipped, Delivered, Cancelled
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: order.items returns the specific products bought
    items = db.relationship('OrderItem', backref='order', lazy=True)

# 5. ORDER ITEM MODEL (The Line Item)
# Connects orders to products and captures the price at the moment of sale
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # PRICE SNAPSHOT: We store the price here so that if you change the product 
    # price in the future, your historical order data remains correct.
    price_at_purchase = db.Column(db.Integer, nullable=False)