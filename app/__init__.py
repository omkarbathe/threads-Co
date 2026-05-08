import os
import urllib.parse
from flask import Flask, session, g
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_login import LoginManager

# 1. Load the .env file immediately
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # 2. Database Configuration
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    connection_string = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        f'Encrypt=yes;'
        f'TrustServerCertificate=yes;'
    )
    params = urllib.parse.quote_plus(connection_string)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 3. Secret Key for Sessions
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    db.init_app(app)
    
    # Import models here to avoid circular imports
    from app.models.models import User

    # --- THE CRITICAL FIX ---
    # This runs BEFORE your route functions, making g.current_user available for Python logic
    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        if user_id:
            g.current_user = User.query.get(user_id)
        else:
            g.current_user = None

    # This makes 'current_user' available in all HTML templates automatically
    @app.context_processor
    def inject_user():
        return dict(current_user=getattr(g, 'current_user', None))
    # ------------------------

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # 5. Register Blueprints
    from app.routes.admin import admin as admin_bp
    app.register_blueprint(admin_bp)

    from app.routes.main import main as main_bp
    app.register_blueprint(main_bp)

    from app.routes.cart import cart as cart_bp
    app.register_blueprint(cart_bp, url_prefix='/cart')
    
    from app.routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app