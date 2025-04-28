from flask import Flask
from flask_limiter import Limiter
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from pathlib import Path
import openai
import pymysql
from .db_operations import DBOperations

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def load_environment():
    """Load environment variables with validation"""
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found at {env_path}")
    load_dotenv(dotenv_path=env_path)


def test_database_connection(config):
    """Test database connection before app starts"""
    try:
        conn = pymysql.connect(
            host=config['DB_HOST'],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            database=config['DB_NAME']
        )
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False

def create_app():
    """Application factory with enhanced configuration"""
    load_environment()
    
    app = Flask(__name__)

    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file")
    from app.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    required_env_vars = ['SECRET_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME']
    for var in required_env_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")
    
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'SQLALCHEMY_DATABASE_URI': f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}",
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_pre_ping': True,
            'pool_recycle': 3600
        }
    })

    if not test_database_connection({
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
        'DB_NAME': os.getenv('DB_NAME')
    }):
        raise RuntimeError("Failed to connect to database")
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print("Database tables verified/created")
        except Exception as e:
            print(f"Error creating tables: {str(e)}")

    # Register blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user: {str(e)}")
            return None

    return app
