from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables FIRST
load_dotenv()





# Initialize the Flask app
app = create_app()
 # Register Blueprints
from app.routes import main
app.register_blueprint(main, url_prefix='/main')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)