# config.py
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configs da Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Configs do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configs do Firestore
FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")

# Configs do Flask
PORT = os.getenv("PORT", default=5000)

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')