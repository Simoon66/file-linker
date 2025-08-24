#!/usr/bin/env python3
"""
Telegram File Sharing Bot with Admin Controls and Channel Membership Verification
"""

import logging
import asyncio

# Import telegram modules with error handling
try:
    from telegram.ext import (
        Application, 
        CommandHandler, 
        MessageHandler, 
        CallbackQueryHandler,
        filters
    )
    print("Telegram imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
    import sys
    sys.exit(1)
from keep_alive import keep_alive

keep_alive()

from config import BOT_TOKEN, DATABASE_PATH
from database import Database
from handlers import BotHandlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot"""
    logger.info("Starting Telegram File Sharing Bot...")
    
    # Initialize database
    database = Database(DATABASE_PATH)
    
    # Initialize handlers
    bot_handlers = BotHandlers(database)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot_handlers.start_command))
    application.add_handler(CommandHandler("stats", bot_handlers.stats_command))
    application.add_handler(CommandHandler("batch_start", bot_handlers.batch_start_command))
    application.add_handler(CommandHandler("batch_end", bot_handlers.batch_end_command))
    application.add_handler(CommandHandler("ban", bot_handlers.ban_command))
    application.add_handler(CommandHandler("unban", bot_handlers.unban_command))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(bot_handlers.callback_query_handler))
    
    # File handlers
    application.add_handler(MessageHandler(filters.Document.ALL, bot_handlers.handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, bot_handlers.handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, bot_handlers.handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, bot_handlers.handle_audio))
    
    # Error handler
    application.add_error_handler(bot_handlers.error_handler)
    
    logger.info("Bot handlers registered successfully")
    
    # Start the bot
    logger.info("Starting bot polling...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
