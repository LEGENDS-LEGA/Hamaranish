import logging
import os
from io import BytesIO
import re
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from pymongo import MongoClient
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PHOTO, WAITING_FOR_TEXT, WAITING_FOR_SEARCH = range(3)

# Get token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN', "8226242752:AAFRhCf-3zcrhKpTs0vSOyCTB77pKIw8NYc")
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

class MongoDBStorage:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client.avto_bot_db
        self.collection = self.db.records
        print("✅ MongoDB connected successfully")

    def save_record(self, file_data, text_data):
        normalized_text = self.normalize_text(text_data)
        
        document = {
            'image_data': file_data,
            'text_data': text_data,
            'normalized_text': normalized_text,
            'created_at': datetime.now()
        }
        
        result = self.collection.insert_one(document)
        print(f"✅ Պահպանվեց համարանիշը: '{text_data}'")
        return True

    def normalize_text(self, text):
        return ' '.join(text.strip().upper().split())

    def search_record(self, search_text):
        normalized_search = self.normalize_text(search_text)
        return self.collection.find_one({'normalized_text': normalized_search})

# ... (rest of your bot class remains the same) ...