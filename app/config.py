import os

from dotenv import load_dotenv
import requests
load_dotenv()  # Loads .env file

class Config:
    # SQL Server Configuration
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}?driver=ODBC+Driver+17+for+SQL+Server"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {'timeout': 30}
    }
HF_TOKEN = os.getenv("HF_TOKEN")  # Ensure this is set in .env
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/facebook/blenderbot-400M-distill"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

def query(payload):
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    

    
    # OpenAI Configuration
    # OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # openai.api_key = os.getenv("OPENAI_API_KEY")
    # OPENAI_MODEL = 'gpt-4o'
    # OPENAI_TEMPERATURE = 0.7
    # OPENAI_MAX_TOKENS = 150

    # @classmethod
    # def validate_config(cls):
    #     """Validate that required config variables exist"""
    #     required = ['SECRET_KEY', 'OPENAI_API_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    #     missing = [var for var in required if not os.getenv(var)]
    #     if missing:
    #         raise ValueError(f"Missing required environment variables: {', '.join(missing)}")