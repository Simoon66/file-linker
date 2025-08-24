from telegram import Update, Bot, CallbackQuery
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import logging
import asyncio
from typing import Tuple

from database import Database
from config import *
from utils import (
    check_channel_membership, 
    create_channel_join_keyboard, 
    generate_share_link,
    get_file_type,
    is_admin,
    log_user_action,
    schedule_file_deletion,
    extract_user_id
)

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, database: Database):
        self.db = database
        self.batch_mode = {}  # Store batch mode state per user
        self.pending_batches = {}  # Store files for batch upload
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        if not user:
            return  # Skip if no user (e.g., channel posts)
        user_id = user.id
        username = user.username or "Unknown"
        
        # Check if user is banned
        if self.db.is_user_banned(user_id):
            await update.message.reply_text(MESSAGES["banned_user"])
            return
        
        log_user_action(user_id, username, "start_command")
        
        # Check if there's a file code in the start parameter
        if context.args:
            file_code = context.args[0]
            await self.handle_file_request(update, context, file_code)
        else:
            # Send welcome message
            await update.message.reply_text(MESSAGES["welcome"])
    
    async def handle_file_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_code: str):
        """Handle file request with code"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        log_user_action(user_id, username, f"file_request:{file_code}")
        
        # Check channel membership first
        is_member, not_joined = await check_channel_membership(context.bot, user_id)
        
        if not is_member:
            keyboard = create_channel_join_keyboard(not_joined, file_code)
            await update.message.reply_text(
                MESSAGES["channel_join_required"],
                reply_markup=keyboard
            )
            return
        
        # Check if it's a single file or batch
        file_data = self.db.get_file(file_code)
        
        if file_data:
            # Single file
            await self.deliver_single_file(update, context, file_data, file_code)
        else:
            # Check if it's a batch
            batch_files = self.db.get_batch_files(file_code)
            if batch_files:
                await self.deliver_batch_files(update, context, batch_files, file_code)
            else:
                await update.message.reply_text(MESSAGES["file_not_found"])
    
    async def deliver_single_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_data, file_code: str):
        """Deliver a single file to user"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        file_id, file_name, file_type, message_id, uploaded_by = file_data
        
        try:
            # Forward the file from storage channel
            sent_msg = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=message_id
            )
            
            # Send delivery confirmation
            await update.message.reply_text(MESSAGES["file_delivered"])
            
            # Schedule deletion after 5 minutes
            asyncio.create_task(schedule_file_deletion(
                context.bot, user_id, [sent_msg.message_id], 300
            ))
            
            log_user_action(user_id, username, f"file_delivered:{file_code}")
            
        except TelegramError as e:
            logger.error(f"Error delivering file {file_code} to user {user_id}: {e}")
            await update.message.reply_text(MESSAGES["error"])
    
    async def deliver_batch_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE, batch_files, file_code: str):
        """Deliver batch files to user"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        message_ids = []
        
        try:
            for file_data in batch_files:
                file_id, file_name, file_type, message_id, uploaded_by = file_data
                
                sent_msg = await context.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=message_id
                )
                message_ids.append(sent_msg.message_id)
            
            # Send batch delivery confirmation
            await update.message.reply_text(MESSAGES["batch_delivered"])
            
            # Schedule deletion after 5 minutes
            asyncio.create_task(schedule_file_deletion(
                context.bot, user_id, message_ids, 300
            ))
            
            log_user_action(user_id, username, f"batch_delivered:{file_code}:{len(batch_files)}")
            
        except TelegramError as e:
            logger.error(f"Error delivering batch {file_code} to user {user_id}: {e}")
            await update.message.reply_text(MESSAGES["error"])
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads from admin"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        # Check if user is admin
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        log_user_action(user_id, username, "document_upload")
        
        # Check if in batch mode
        if user_id in self.batch_mode:
            await self.add_file_to_batch(update, context, 'document')
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(MESSAGES["processing"])
        
        try:
            document = update.message.document
            file_name = document.file_name or "Unknown"
            file_type = get_file_type(document)
            file_id = document.file_id
            
            # Forward file to storage channel
            forwarded = await context.bot.copy_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Save to database
            file_code = self.db.save_file(
                file_id=file_id,
                file_name=file_name,
                file_type=file_type,
                message_id=forwarded.message_id,
                uploaded_by=user_id
            )
            
            # Generate share link
            bot_info = await context.bot.get_me()
            share_link = generate_share_link(bot_info.username, file_code)
            
            # Update processing message with success
            await processing_msg.edit_text(
                MESSAGES["file_uploaded"].format(link=share_link)
            )
            
            log_user_action(user_id, username, f"document_uploaded:{file_code}")
            
        except Exception as e:
            logger.error(f"Error processing document from user {user_id}: {e}")
            await processing_msg.edit_text(MESSAGES["error"])
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads from admin"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        log_user_action(user_id, username, "photo_upload")
        
        # Check if in batch mode
        if user_id in self.batch_mode:
            await self.add_file_to_batch(update, context, 'photo')
            return
        
        processing_msg = await update.message.reply_text(MESSAGES["processing"])
        
        try:
            photo = update.message.photo[-1]  # Get highest quality
            file_id = photo.file_id
            file_name = f"photo_{photo.file_unique_id}.jpg"
            file_type = "image/jpeg"
            
            # Forward to storage channel
            forwarded = await context.bot.copy_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Save to database
            file_code = self.db.save_file(
                file_id=file_id,
                file_name=file_name,
                file_type=file_type,
                message_id=forwarded.message_id,
                uploaded_by=user_id
            )
            
            # Generate share link
            bot_info = await context.bot.get_me()
            share_link = generate_share_link(bot_info.username, file_code)
            
            await processing_msg.edit_text(
                MESSAGES["file_uploaded"].format(link=share_link)
            )
            
            log_user_action(user_id, username, f"photo_uploaded:{file_code}")
            
        except Exception as e:
            logger.error(f"Error processing photo from user {user_id}: {e}")
            await processing_msg.edit_text(MESSAGES["error"])
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video uploads from admin"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        log_user_action(user_id, username, "video_upload")
        
        # Check if in batch mode
        if user_id in self.batch_mode:
            await self.add_file_to_batch(update, context, 'video')
            return
        
        processing_msg = await update.message.reply_text(MESSAGES["processing"])
        
        try:
            video = update.message.video
            file_id = video.file_id
            file_name = video.file_name or f"video_{video.file_unique_id}.mp4"
            file_type = get_file_type(video)
            
            # Forward to storage channel
            forwarded = await context.bot.copy_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Save to database
            file_code = self.db.save_file(
                file_id=file_id,
                file_name=file_name,
                file_type=file_type,
                message_id=forwarded.message_id,
                uploaded_by=user_id
            )
            
            # Generate share link
            bot_info = await context.bot.get_me()
            share_link = generate_share_link(bot_info.username, file_code)
            
            await processing_msg.edit_text(
                MESSAGES["file_uploaded"].format(link=share_link)
            )
            
            log_user_action(user_id, username, f"video_uploaded:{file_code}")
            
        except Exception as e:
            logger.error(f"Error processing video from user {user_id}: {e}")
            await processing_msg.edit_text(MESSAGES["error"])
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio uploads from admin"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "Unknown"
        
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        log_user_action(user_id, username, "audio_upload")
        
        # Check if in batch mode
        if user_id in self.batch_mode:
            await self.add_file_to_batch(update, context, 'audio')
            return
        
        processing_msg = await update.message.reply_text(MESSAGES["processing"])
        
        try:
            audio = update.message.audio
            file_id = audio.file_id
            file_name = audio.file_name or f"audio_{audio.file_unique_id}.mp3"
            file_type = get_file_type(audio)
            
            # Forward to storage channel
            forwarded = await context.bot.copy_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Save to database
            file_code = self.db.save_file(
                file_id=file_id,
                file_name=file_name,
                file_type=file_type,
                message_id=forwarded.message_id,
                uploaded_by=user_id
            )
            
            # Generate share link
            bot_info = await context.bot.get_me()
            share_link = generate_share_link(bot_info.username, file_code)
            
            await processing_msg.edit_text(
                MESSAGES["file_uploaded"].format(link=share_link)
            )
            
            log_user_action(user_id, username, f"audio_uploaded:{file_code}")
            
        except Exception as e:
            logger.error(f"Error processing audio from user {user_id}: {e}")
            await processing_msg.edit_text(MESSAGES["error"])
    
    async def batch_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start batch upload mode"""
        user = update.effective_user
        user_id = user.id
        
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        self.batch_mode[user_id] = True
        self.pending_batches[user_id] = []
        
        await update.message.reply_text(MESSAGES["batch_mode_start"])
    
    async def batch_end_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """End batch upload mode and create batch link"""
        user = update.effective_user
        user_id = user.id
        
        if not is_admin(user_id) or user_id not in self.batch_mode:
            return
        
        if user_id not in self.pending_batches or not self.pending_batches[user_id]:
            await update.message.reply_text("No files in batch!")
            return
        
        # Create batch group
        batch_name = f"Batch_{len(self.pending_batches[user_id])}_files"
        batch_id = self.db.create_batch_group(batch_name, user_id)
        
        # Save all files with batch_id
        file_count = 0
        for file_info in self.pending_batches[user_id]:
            self.db.save_file(
                file_id=file_info['file_id'],
                file_name=file_info['file_name'],
                file_type=file_info['file_type'],
                message_id=file_info['message_id'],
                uploaded_by=user_id,
                batch_id=batch_id
            )
            file_count += 1
        
        # Generate share link
        bot_info = await context.bot.get_me()
        share_link = generate_share_link(bot_info.username, batch_id)
        
        # Clean up
        del self.batch_mode[user_id]
        del self.pending_batches[user_id]
        
        await update.message.reply_text(
            MESSAGES["batch_uploaded"].format(count=file_count, link=share_link)
        )
    
    async def add_file_to_batch(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_type_name: str):
        """Add file to current batch"""
        user = update.effective_user
        user_id = user.id
        
        try:
            # Get file info based on type
            file_obj = None
            file_name = "Unknown"
            
            if file_type_name == 'document':
                file_obj = update.message.document
                file_name = file_obj.file_name or "Unknown"
            elif file_type_name == 'photo':
                file_obj = update.message.photo[-1]
                file_name = f"photo_{file_obj.file_unique_id}.jpg"
            elif file_type_name == 'video':
                file_obj = update.message.video
                file_name = file_obj.file_name or f"video_{file_obj.file_unique_id}.mp4"
            elif file_type_name == 'audio':
                file_obj = update.message.audio
                file_name = file_obj.file_name or f"audio_{file_obj.file_unique_id}.mp3"
            
            if not file_obj:
                return
            
            file_type = get_file_type(file_obj)
            file_id = file_obj.file_id
            
            # Forward file to storage channel
            forwarded = await context.bot.copy_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Store in pending batch
            self.pending_batches[user_id].append({
                'file_id': file_id,
                'file_name': file_name,
                'file_type': file_type,
                'message_id': forwarded.message_id
            })
            
            await update.message.reply_text(
                f"✅ Added to batch ({len(self.pending_batches[user_id])} files)"
            )
            
        except Exception as e:
            logger.error(f"Error adding file to batch: {e}")
            await update.message.reply_text(MESSAGES["error"])
    
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban a user"""
        user = update.effective_user
        user_id = user.id
        
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /ban <user_id>")
            return
        
        target_user_id = extract_user_id(context.args[0])
        if not target_user_id or target_user_id == 0:
            await update.message.reply_text(MESSAGES["user_not_found"])
            return
        
        self.db.ban_user(target_user_id, user_id)
        await update.message.reply_text(
            MESSAGES["user_banned"].format(user_id=target_user_id)
        )
    
    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban a user"""
        user = update.effective_user
        user_id = user.id
        
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /unban <user_id>")
            return
        
        target_user_id = extract_user_id(context.args[0])
        if not target_user_id or target_user_id == 0:
            await update.message.reply_text(MESSAGES["user_not_found"])
            return
        
        self.db.unban_user(target_user_id)
        await update.message.reply_text(
            MESSAGES["user_unbanned"].format(user_id=target_user_id)
        )
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries (button presses)"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("retry_"):
            file_code = query.data[6:]  # Remove "retry_" prefix
            
            # Create a new update object to simulate /start command
            new_update = Update(
                update_id=update.update_id,
                message=query.message,
                callback_query=None
            )
            
            # Set context args to simulate /start with file_code
            context.args = [file_code]
            
            await self.handle_file_request(new_update, context, file_code)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command for admin"""
        user = update.effective_user
        user_id = user.id
        
        if not is_admin(user_id):
            await update.message.reply_text(MESSAGES["not_admin"])
            return
        
        stats = self.db.get_file_stats()
        stats_text = f"📊 বট পরিসংখ্যান / Bot Statistics:\n\n"
        stats_text += f"📁 মোট ফাইল / Total Files: {stats['total_files']}\n"
        stats_text += f"🚫 ব্যান ইউজার / Banned Users: {stats['total_banned']}\n"
        stats_text += f"📦 ব্যাচ গ্রুপ / Batch Groups: {stats['total_batches']}\n"
        
        await update.message.reply_text(stats_text)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        if update and update.effective_user:
            logger.error(f"Update from user {update.effective_user.id} caused error {context.error}")
        else:
            logger.error(f"Update caused error {context.error}")
