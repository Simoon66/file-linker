import os

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7918521477:AAE5Nm04alKrgNQ6LAl83xKyYmdgqJ_aPL4")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "7019013170"))
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", "-1002921970479"))

# Required channels for membership verification  
REQUIRED_CHANNELS = [
    {"name": "Channel 1", "url": "https://t.me/+TqNWX2cXQ6w4ZDFl"},
    {"name": "@Anime_Hub_Official_1", "url": "https://t.me/Anime_Hub_Official_1"},
    {"name": "Channel 3", "url": "https://t.me/Anime_Hub_Official_Movies"}, 
    {"name": "Group 4", "url": "https://t.me/+7u_LdxSkRUwzMmM9"}
]

# Database configuration
DATABASE_PATH = "filebot.db"

# Messages in Bengali and English
MESSAGES = {
    "not_admin": "🚫 দুঃখিত! আপনি এই বট ব্যবহার করার অনুমতি নেই।\n\nSorry! You are not authorized to use this bot.",
    "banned_user": "⛔ আপনি এই বট ব্যবহার করতে নিষিদ্ধ।\n\n⛔ You are banned from using this bot.",
    "file_uploaded": "✅ ফাইল সফলভাবে আপলোড হয়েছে!\n\n🔗 শেয়ার লিংক: {link}\n\n✅ File uploaded successfully!\n\n🔗 Share Link: {link}",
    "batch_uploaded": "✅ {count}টি ফাইল সফলভাবে আপলোড হয়েছে!\n\n🔗 শেয়ার লিংক: {link}\n\n✅ {count} files uploaded successfully!\n\n🔗 Share Link: {link}",
    "channel_join_required": "⚠️ ফাইল পেতে নিচের চ্যানেলগুলোতে জয়েন করুন:\n\n⚠️ Please join these channels to get the file:",
    "file_not_found": "❌ ফাইল পাওয়া যায়নি বা লিংক ভুল।\n\n❌ File not found or invalid link.",
    "welcome": "🤖 স্বাগতম ফাইল শেয়ার বটে!\n\nAdmin রা ফাইল পাঠালে আমি শেয়ার লিংক তৈরি করি।\n\n🤖 Welcome to File Share Bot!\n\nAdmins can send files and I'll create share links.",
    "processing": "⏳ ফাইল প্রসেসিং হচ্ছে...\n\n⏳ Processing file...",
    "batch_mode_start": "📦 ব্যাচ মোড চালু হয়েছে! এখন একটার পর একটা ফাইল পাঠান। শেষ হলে /batch_end দিন।\n\n📦 Batch mode started! Send files one by one. Send /batch_end when done.",
    "batch_mode_end": "📦 ব্যাচ মোড বন্ধ হয়েছে।\n\n📦 Batch mode ended.",
    "file_delivered": "📁 ফাইল পাঠানো হয়েছে!\n\n⚠️ এই ফাইল 5 মিনিট পর মুছে যাবে। দরকার হলে অন্য কোথাও ফরওয়ার্ড করে রাখুন।\n\n📁 File delivered!\n\n⚠️ This file will be deleted in 5 minutes. Forward it somewhere if needed.",
    "batch_delivered": "📦 সব ফাইল পাঠানো হয়েছে!\n\n⚠️ এই ফাইলগুলো 5 মিনিট পর মুছে যাবে। দরকার হলে অন্য কোথাও ফরওয়ার্ড করে রাখুন।\n\n📦 All files delivered!\n\n⚠️ These files will be deleted in 5 minutes. Forward them somewhere if needed.",
    "user_banned": "✅ User {user_id} কে ban করা হয়েছে।\n\n✅ User {user_id} has been banned.",
    "user_unbanned": "✅ User {user_id} এর ban উঠানো হয়েছে।\n\n✅ User {user_id} has been unbanned.",
    "user_not_found": "❌ User ID টি সঠিক নয়।\n\n❌ Invalid User ID.",
    "error": "❌ কোন সমস্যা হয়েছে। আবার চেষ্টা করুন।\n\n❌ Something went wrong. Please try again."
}
