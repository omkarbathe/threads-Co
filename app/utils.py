    # app/utils.py
from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            # NOTE: We use 'auth.login' here. Since 'utils' doesn't 
            # import auth, this string reference is safe.
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Pull the user from the DB to get the LATEST is_admin status
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash("Access Denied: Admin privileges required.", "danger")
            return redirect(url_for('main.home'))
            
        return f(*args, **kwargs)
    return decorated_function