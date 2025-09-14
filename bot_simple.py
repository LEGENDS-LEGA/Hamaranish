import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PHOTO, WAITING_FOR_TEXT = range(2)

# Replace this with your actual bot token from @BotFather
BOT_TOKEN = "8226242752:AAFRhCf-3zcrhKpTs0vSOyCTB77pKIw8NYc"

class SimpleStorage:
    """Simple in-memory storage for testing"""
    def __init__(self):
        self.records = []
        print("✅ Using simple memory storage")
    
    def save_record(self, file_data, text_data):
        self.records.append({
            'file_data': file_data,
            'text_data': text_data
        })
        return True
    
    def search_record(self, search_text):
        for record in self.records:
            if record['text_data'] == search_text:
                return record
        return None

class TelegramBot:
    def __init__(self):
        if BOT_TOKEN == "8226242752:AAFRhCf-3zcrhKpTs0vSOyCTB77pKIw8NYc":
            raise ValueError("❌ Please replace BOT_TOKEN with your actual bot token from @BotFather")
        
        self.storage = SimpleStorage()
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send instructions when command /start is issued."""
        await update.message.reply_text(
            "🚗 Please send me a photo and the related data (e.g., 44 AN 444)\n\n"
            "First, send the photo, then send the text data."
        )
        return WAITING_FOR_PHOTO

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle received photo."""
        # Store photo in context
        photo = update.message.photo[-1]
        file = await photo.get_file()
        context.user_data['photo_data'] = await file.download_as_bytearray()
        
        await update.message.reply_text(
            "📸 Photo received! Now please send the text data (e.g., 44 AN 444):"
        )
        return WAITING_FOR_TEXT

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle received text after photo."""
        text_data = update.message.text.strip()
        
        if 'photo_data' not in context.user_data:
            await update.message.reply_text("❌ Please send a photo first!")
            return ConversationHandler.END
        
        # Save to storage
        try:
            photo_data = context.user_data['photo_data']
            self.storage.save_record(photo_data, text_data)
            
            await update.message.reply_text(
                f"✅ Successfully saved!\n"
                f"📝 Text: {text_data}\n"
                f"📸 Photo stored"
            )
            
            # Clean up
            context.user_data.clear()
            
        except Exception as e:
            logger.error(f"Error saving record: {e}")
            await update.message.reply_text("❌ Error saving. Please try again.")
        
        return ConversationHandler.END

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for records by text."""
        if not context.args:
            await update.message.reply_text("❌ Please provide search text. Example: /search 44 AN 444")
            return
        
        search_text = ' '.join(context.args).strip()
        
        try:
            result = self.storage.search_record(search_text)
            
            if not result:
                await update.message.reply_text("❌ No record found.")
                return
            
            # Send the photo with caption
            await update.message.reply_photo(
                photo=result['file_data'],
                caption=f"🔍 Found record:\n📝 {result['text_data']}"
            )
                
        except Exception as e:
            logger.error(f"Error searching: {e}")
            await update.message.reply_text("❌ Error searching. Please try again.")

    def run(self):
        """Run the bot."""
        print("🤖 Bot is running...")
        print("Use /start to save photo + text")
        print("Use /search <text> to search records")
        self.application.run_polling()

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()