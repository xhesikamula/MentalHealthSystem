from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
import os
from dotenv import load_dotenv
from pathlib import Path
import openai
import pymysql

from .dal.db_operations import DBOperations

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

# def create_app():
#     """Application factory with enhanced configuration"""
#     load_environment()
    
#     app = Flask(__name__, template_folder='view/templates', static_folder='view/static')

#     # OpenAI API key validation
#     openai.api_key = os.getenv('OPENAI_API_KEY')
#     if not openai.api_key:
#         raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file")

#     # Register admin blueprint early
#     from app.controllers.admin_routes import admin_bp
#     app.register_blueprint(admin_bp)

#     # Validate required environment variables
#     required_env_vars = ['SECRET_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME']
#     for var in required_env_vars:
#         if not os.getenv(var):
#             raise ValueError(f"Missing required environment variable: {var}")
        
    
    
#     # SQLAlchemy setup
#     app.config.update({
#         'SECRET_KEY': os.getenv('SECRET_KEY'),
#         'SQLALCHEMY_DATABASE_URI': f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}",
#         'SQLALCHEMY_TRACK_MODIFICATIONS': False,
#         'SQLALCHEMY_ENGINE_OPTIONS': {
#             'pool_pre_ping': True,
#             'pool_recycle': 3600
#         }
#     })

#     if not test_database_connection({
#         'DB_HOST': os.getenv('DB_HOST'),
#         'DB_USER': os.getenv('DB_USER'),
#         'DB_PASSWORD': os.getenv('DB_PASSWORD'),
#         'DB_NAME': os.getenv('DB_NAME')
#     }):
#         raise RuntimeError("Failed to connect to database")

#     # Initialize extensions
#     db.init_app(app)
#     migrate.init_app(app, db)
#     login_manager.init_app(app)
#     login_manager.login_view = 'main.login'

#     # Auto-create tables
#     with app.app_context():
#         try:
#             db.create_all()
#             print("Database tables verified/created")
#         except Exception as e:
#             print(f"Error creating tables: {str(e)}")

#     # Register main blueprint
#     from app.controllers.routes import main as main_blueprint
#     app.register_blueprint(main_blueprint)

#     # User loader for Flask-Login
#     from app.model.models import User
def create_app():
    """Application factory with enhanced configuration"""
    load_environment()
    
    app = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # OpenAI API key validation
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file")

    # Register admin blueprint early
    from app.controllers.admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    # Validate required environment variables
    required_env_vars = ['SECRET_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME']
    for var in required_env_vars:
        value = os.getenv(var)
        if value is None:
            raise ValueError(f"Missing required environment variable: {var}")
        if var != 'DB_PASSWORD' and value == '':
            raise ValueError(f"Environment variable {var} cannot be empty")
        
    # Configure app
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

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Import your User model here
    from app.model.models import User

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Auto-create tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables verified/created")
        except Exception as e:
            print(f"Error creating tables: {str(e)}")

    # Register main blueprint
    from app.controllers.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app


    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user: {str(e)}")
            return None

    from flask_login import current_user

    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            notifications = DBOperations.get_pending_notifications(current_user.user_id)
            # Add a dummy notification for testing
            notifications.append({'notification_id': 0, 'message': 'This is a test notification!'})
            return dict(pending_notifications=notifications)
        return dict(pending_notifications=[])

    @app.before_request
    def mark_seen_notifications():
        if current_user.is_authenticated:
            notifications = DBOperations.get_pending_notifications(current_user.user_id)
            if notifications:
                ids = [n['notification_id'] for n in notifications]
                DBOperations.mark_notifications_sent(ids)

    # Start the background task scheduler
    from tasks import start_scheduler
    start_scheduler(app)

    return app