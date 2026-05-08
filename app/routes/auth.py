from flask import Blueprint, render_template, redirect, url_for, session , request,flash,current_app
import os,requests,jwt
from app import db
from app.models.models import User


auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    # Building the URL from your .env variables
    domain = os.getenv('COGNITO_DOMAIN')
    client_id = os.getenv('COGNITO_APP_CLIENT_ID')
    redirect_uri = os.getenv('COGNITO_REDIRECT_URI')
    
    # This creates the final link to your Hosted UI
    login_url = (
        f"https://{domain}/login?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=email+openid+phone&"
        f"redirect_uri={redirect_uri}"
    )
    return redirect(login_url)


@auth.route('/callback')
def callback():
    # 1. Get the Authorization Code from Cognito
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400

    # 2. Setup Token Exchange
    domain = os.getenv('COGNITO_DOMAIN')
    if not domain.startswith('http'):
        domain = f"https://{domain}"

    token_url = f"{domain}/oauth2/token"
    
    data = {
        'grant_type': 'authorization_code',
        'client_id': os.getenv('COGNITO_APP_CLIENT_ID'),
        'client_secret': os.getenv('COGNITO_APP_CLIENT_SECRET'),
        'code': code,
        'redirect_uri': os.getenv('COGNITO_REDIRECT_URI')
    }
    
    # 3. Exchange Code for Tokens
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status() 
        tokens = response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Cognito Exchange Failed: {e}")
        return f"Authentication Error", 400

    id_token = tokens.get('id_token')
    if not id_token:
        return "Error: Missing id_token", 400

    # 4. Decode Token
    try:
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        email = decoded_token.get('email')
        cognito_user_id = decoded_token.get('sub') 
    except jwt.DecodeError:
        return "Error: JWT Decode Failed", 400

    # 5. RDS User Persistence
    user = User.query.get(cognito_user_id)

    if not user:
        # Create new user record
        user = User(
            id=cognito_user_id, 
            email=email,
            is_onboarded=False, # Force to setup
            is_admin=False 
        )
        db.session.add(user)
        db.session.commit()
    
    # 6. SESSION SYNC
    session.permanent = True
    session['user_id'] = user.id
    session['email'] = user.email
    session['is_admin'] = user.is_admin
    session['is_onboarded'] = user.is_onboarded

    # Determine display name
    if user.first_name and user.last_name:
        session['user_name'] = f"{user.first_name} {user.last_name}"
    elif user.first_name:
        session['user_name'] = user.first_name
    else:
        session['user_name'] = email.split('@')[0].title()

    # 7. ROUTING LOGIC (The Fix)
    
    # Priority A: Admins go straight to management
    if user.is_admin:
        flash(f"Welcome to the Atelier Command Center, {session['user_name']}", "success")
        return redirect(url_for('admin.dashboard'))

    # Priority B: Non-onboarded customers must finish setup
    if not user.is_onboarded:
        flash("Please complete your profile to continue.", "info")
        return redirect(url_for('auth.complete_profile'))

    # Priority C: Onboarded customers go to the gallery
    flash(f"Welcome back, {session['user_name']}", "success")
    return redirect(url_for('main.home'))


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))


@auth.route('/complete-profile', methods=['GET', 'POST'])
def complete_profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    
    if request.method == 'POST':
        # Update existing user data with form data
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')
        user.city = request.form.get('city')
        user.pincode = request.form.get('pincode')
        
        user.is_onboarded = True  # Ensure this is set to true
        db.session.commit()
        
        # Update the session name in case they changed their name
        session['user_name'] = f"{user.first_name} {user.last_name}"
        
        flash("Profile updated successfully.", "success")
        return redirect(url_for('main.profile')) # Redirect back to profile view

    # Pass the user object to the template so the form can be pre-filled
    return render_template('auth/complete_profile.html', user=user)