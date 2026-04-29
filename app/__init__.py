import os
import urllib.parse
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# 1. Load the .env file immediately
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # 2. Database Configuration (Pulling from .env)
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
    
    # 3. Secret Key for Sessions
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    db.init_app(app)

    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')


    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    return app