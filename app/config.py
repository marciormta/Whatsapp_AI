import os
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis definidas no .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")
VERIFICATION_TOKEN = os.getenv("VERIFICATION_TOKEN", "8094283409423")
APP_PORT = os.getenv("APP_PORT", "8005")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
