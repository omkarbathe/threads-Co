from datetime import datetime
from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(100), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.Unicode(50))
    last_name = db.Column(db.Unicode(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    is_onboarded = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cart_items = db.relationship('CartItem', back_populates='user', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='customer', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False)
    slug = db.Column(db.Unicode(100), unique=True)
    description = db.Column(db.UnicodeText)
    image_url = db.Column(db.Unicode(500))
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.Unicode(50), unique=True)
    name = db.Column(db.Unicode(100), nullable=False)
    story = db.Column(db.UnicodeText)
    material = db.Column(db.Unicode(200))
    origin = db.Column(db.Unicode(100))
    price = db.Column(db.Integer, nullable=False) 
    gender = db.Column(db.Unicode(20), nullable=False)
    collection_tag = db.Column(db.Unicode(50))
    image_url = db.Column(db.Unicode(500), nullable=False)
    image_alt = db.Column(db.Unicode(500))
    is_featured = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # CASCADE here ensures Variants are deleted when Product is deleted
    variants = db.relationship(
        'ProductVariant', 
        backref='product', 
        lazy=True,
        cascade="all, delete-orphan"
    )

class ProductVariant(db.Model):
    __tablename__ = 'product_variants'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    size = db.Column(db.Unicode(20), nullable=False)
    stock = db.Column(db.Integer, default=0)
    
    # CASCADE here ensures CartItems are deleted when a Variant is deleted
    cart_items = db.relationship(
        'CartItem', 
        back_populates='variant', 
        lazy=True, 
        cascade="all, delete-orphan"
    )
    
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Use back_populates to avoid the "ArgumentError: property of that name exists"
    variant = db.relationship('ProductVariant', back_populates='cart_items')
    user = db.relationship('User', back_populates='cart_items')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_at_purchase = db.Column(db.Integer, nullable=False)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to User if logged in, otherwise None
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=True)
    
    name = db.Column(db.Unicode(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.Unicode(100), nullable=False)
    message = db.Column(db.UnicodeText, nullable=False)
    
    # Status for admin tracking (Pending, Read, Archived)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional relationship to link back to the user object
    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))

    def __repr__(self):
        return f'<Feedback {self.subject} from {self.email}>'    