import hashlib
import random
import string
import asyncio
from typing import Tuple
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from config import REQUIRED_CHANNELS
import logging

logger = logging.getLogger(__name__)

def generate_share_link(bot_username: str, file_code: str) -> str:
    """Generate shareable link for the file"""
    return f"https://t.me/{bot_username}?start={file_code}"

async def check_channel_membership(bot: Bot, user_id: int) -> Tuple[bool, list]:
    """Check if user is member of all required channels"""
    not_joined = []
    
    # For now, skip membership check - will implement after getting actual channel IDs
    # Temporary: allow all users to access files
    return True, []
    
    for i, channel_id in enumerate(channel_ids):
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            # Check if user is member (not left or kicked)
            if member.status in ['left', 'kicked']:
                not_joined.append(REQUIRED_CHANNELS[i])
        except TelegramError as e:
            logger.error(f"Error checking membership for {channel_id}: {e}")
            not_joined.append(REQUIRED_CHANNELS[i])
    
    is_member = len(not_joined) == 0
    return is_member, not_joined

def create_channel_join_keyboard(not_joined_channels: list, file_code: str = None) -> InlineKeyboardMarkup:
    """Create inline keyboard with channel join buttons"""
    keyboard = []
    
    # Add channel join buttons (2 per row)
    for i in range(0, len(not_joined_channels), 2):
        row = []
        for j in range(2):
            if i + j < len(not_joined_channels):
                channel = not_joined_channels[i + j]
                row.append(InlineKeyboardButton(
                    f"Join {channel['name']}",
                    url=channel['url']
                ))
        keyboard.append(row)
    
    # Add retry button if file_code is provided
    if file_code:
        keyboard.append([
            InlineKeyboardButton(
                "🔄 Retry / পুনরায় চেষ্টা করুন",
                callback_data=f"retry_{file_code}"
            )
        ])
    
    return InlineKeyboardMarkup(keyboard)

def get_file_type(file_obj) -> str:
    """Determine file type from telegram file object"""
    if hasattr(file_obj, 'mime_type') and file_obj.mime_type:
        return file_obj.mime_type
    elif hasattr(file_obj, 'file_name') and file_obj.file_name:
        extension = file_obj.file_name.split('.')[-1].lower()
        mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'mp4': 'video/mp4',
            'mp3': 'audio/mpeg',
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed'
        }
        return mime_types.get(extension, 'application/octet-stream')
    return 'unknown'

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    from config import ADMIN_USER_ID
    return user_id == ADMIN_USER_ID

def extract_user_id(text: str) -> int:
    """Extract user ID from command text"""
    try:
        # Handle @username or direct ID
        if text.startswith('@'):
            # In real implementation, you'd need to resolve username to ID
            # For now, just handle direct IDs
            raise ValueError("Username resolution not implemented")
        return int(text)
    except ValueError:
        return 0

async def schedule_file_deletion(bot: Bot, chat_id: int, message_ids: list, delay: int = 300):
    """Schedule file deletion after specified delay (default 5 minutes)"""
    await asyncio.sleep(delay)
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id, message_id)
            logger.info(f"Deleted message {message_id} from chat {chat_id}")
        except TelegramError as e:
            logger.error(f"Failed to delete message {message_id}: {e}")

def log_user_action(user_id: int, username: str, action: str):
    """Log user actions"""
    logger.info(f"User {user_id} (@{username}) performed action: {action}")
