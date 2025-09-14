import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)
from io import BytesIO
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PHOTO, WAITING_FOR_TEXT = range(2)

# Your actual bot token
BOT_TOKEN = "8226242752:AAFRhCf-3zcrhKpTs0vSOyCTB77pKIw8NYc"

class SimpleStorage:
    """Simple storage that mimics database behavior"""
    def __init__(self):
        self.records = {}
        print("✅ Storage initialized")
    
    def save_record(self, file_data, text_data):
        """Save photo and text"""
        # Normalize the text (remove extra spaces, make consistent)
        normalized_text = self.normalize_text(text_data)
        self.records[normalized_text] = {
            'file_data': file_data,
            'text_data': text_data,  # Keep original text for display
            'normalized_text': normalized_text
        }
        print(f"✅ Saved record: '{text_data}' (normalized: '{normalized_text}')")
        return True
    
    def normalize_text(self, text):
        """Normalize text for better searching"""
        # Remove extra spaces, convert to uppercase
        return ' '.join(text.strip().upper().split())
    
    def search_record(self, search_text):
        """Search for records with flexible matching"""
        normalized_search = self.normalize_text(search_text)
        print(f"🔍 Searching for: '{search_text}' (normalized: '{normalized_search}')")
        print(f"Available records: {list(self.records.keys())}")
        
        # First try exact match
        if normalized_search in self.records:
            return self.records[normalized_search]
        
        # If not found, try to find similar records
        for key, record in self.records.items():
            if normalized_search in key or key in normalized_search:
                return record
        
        return None

class TelegramBot:
    def __init__(self):
        self.storage = SimpleStorage()
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    def validate_format(self, text):
        """Validate text format: NN LL NNN or NNN LL NN"""
        # Pattern for NN LL NNN (two digits, space, two uppercase letters, space, three digits)
        pattern1 = r'^\d{2} [A-Z]{2} \d{3}$'
        
        # Pattern for NNN LL NN (three digits, space, two uppercase letters, space, two digits)
        pattern2 = r'^\d{3} [A-Z]{2} \d{2}$'
        
        # Check if text matches either pattern
        if re.match(pattern1, text) or re.match(pattern2, text):
            return True
        return False
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send instructions when command /start is issued."""
        await update.message.reply_text(
            "Please send me a photo and the related data.\n\n"
            "Format must be:\n"
            "• NN LL NNN (e.g., 44 AN 444)\n"
            "• NNN LL NN (e.g., 444 AN 44)"
        )
        return WAITING_FOR_PHOTO

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle received photo."""
        # Store photo in context
        photo = update.message.photo[-1]
        file = await photo.get_file()
        photo_data = await file.download_as_bytearray()
        context.user_data['photo_data'] = photo_data
        
        await update.message.reply_text(
            "Now please send the text data.\n\n"
            "Valid formats:\n"
            "• NN LL NNN (e.g., 44 AN 444)\n"
            "• NNN LL NN (e.g., 444 AN 44)"
        )
        return WAITING_FOR_TEXT

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle received text after photo."""
        text_data = update.message.text.strip()
        
        if 'photo_data' not in context.user_data:
            await update.message.reply_text("Please send a photo first.")
            return ConversationHandler.END
        
        # Validate format
        if not self.validate_format(text_data):
            await update.message.reply_text(
                "Invalid format. Please use NN LL NNN or NNN LL NN.\n\n"
                "Examples:\n"
                "• 44 AN 444\n"
                "• 444 AN 44"
            )
            return WAITING_FOR_TEXT
        
        # Save to storage
        try:
            photo_data = context.user_data['photo_data']
            self.storage.save_record(photo_data, text_data)
            
            await update.message.reply_text("Data saved successfully.")
            
            # Clean up
            context.user_data.clear()
            
        except Exception as e:
            logger.error(f"Error saving record: {e}")
            await update.message.reply_text("Error saving data. Please try again.")
        
        return ConversationHandler.END

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for records by text."""
        if not context.args:
            await update.message.reply_text("Please provide search text. Example: /search 44 AN 444")
            return
        
        search_text = ' '.join(context.args).strip()
        
        # Validate search format
        if not self.validate_format(search_text):
            await update.message.reply_text(
                "Invalid search format. Please use NN LL NNN or NNN LL NN.\n\n"
                "Examples:\n"
                "• /search 44 AN 444\n"
                "• /search 444 AN 44"
            )
            return
        
        try:
            result = self.storage.search_record(search_text)
            
            if not result:
                await update.message.reply_text("No record found.")
                return
            
            # Send only the photo with the exact stored text
            photo_bytes = BytesIO(result['file_data'])
            photo_bytes.name = 'photo.jpg'
            
            await update.message.reply_photo(
                photo=photo_bytes,
                caption=result['text_data']  # Use original text for display
            )
                
        except Exception as e:
            logger.error(f"Error searching: {e}")
            await update.message.reply_text("Error searching. Please try again.")

    def run(self):
        """Run the bot."""
        print("Bot is running...")
        self.application.run_polling()

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()