import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db, create_app

# Create the app instance
app = create_app()

# Use the app context to create the tables
with app.app_context():
    db.create_all()  # This will create all tables defined in your models
