import os
from dotenv import load_dotenv
import requests

# Load environment variables from the .env file
load_dotenv()

class Config:
    # SQL Server Configuration
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}?driver=ODBC+Driver+17+for+SQL+Server"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {'timeout': 30}
    }

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-3.5-turbo'
    OPENAI_TEMPERATURE = 0.7
    OPENAI_MAX_TOKENS = 150

    # Hugging Face Configuration
    HF_TOKEN = os.getenv("HF_TOKEN")  # Ensure this is set in .env
    HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/facebook/blenderbot-400M-distill"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')

    @classmethod
    def validate_config(cls):
        """Validate that required config variables exist"""
        required = ['SECRET_KEY', 'OPENAI_API_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'HF_TOKEN']
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @classmethod
    def get_openai_key(cls):
        """Get OpenAI API key."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")
        return cls.OPENAI_API_KEY

    @classmethod
    def query_huggingface(cls, payload):
        """Query Hugging Face API."""
        response = requests.post(cls.HF_API_URL, headers=cls.headers, json=payload)
        return response.json()
