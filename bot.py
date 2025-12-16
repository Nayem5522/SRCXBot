#--- START OF FILE bot.py ---

import os
import re
import logging
from os import environ
import asyncio
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
from utils import screenshot_video, screenshot_document, extract_filename, progress_bar
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from pytz import timezone
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

id_pattern = re.compile(r'^.\d+$')

# Bot configurations from Environment Variables
AUTH_CHANNEL = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('AUTH_CHANNEL', '-1002245813234').split()] 
api_id = int(os.getenv("API_ID", "12345"))
api_hash = os.getenv("API_HASH", "your_api_hash")
bot_token = os.getenv("BOT_TOKEN", "your_bot_token")
mongo_url = os.getenv("MONGO_DB_URI", "mongodb://localhost:27017")
OWNER_ID = int(os.getenv("OWNER_ID", "5926160191"))  # Bot Owner's User ID
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "-1002196408894")) # Log Channel ID

async def is_subscribed(bot, query, channel):
    btn = []
    for id in channel:
        try:
            chat = await bot.get_chat(int(id))
            await bot.get_chat_member(id, query.from_user.id)
        except UserNotParticipant:
            btn.append([InlineKeyboardButton(f"✇ Join {chat.title} ✇", url=chat.invite_link)])
        except Exception as e:
            logger.error(f"[is_subscribed Error] {e}")
            pass
    return btn

# Pyrogram client init
app = Client("advanced_screenshot_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# MongoDB Setup
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client["screenshot_bot"]
tasks = db["tasks"]

async def check_db_connection():
    """Checks if the MongoDB connection is successful."""
    try:
        await db.command('ping')
        logger.info("✅ MongoDB connection successful.")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        # Optionally exit if DB connection is critical
        # exit(1)


@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    if AUTH_CHANNEL:
        try:
            btn = await is_subscribed(client, message, AUTH_CHANNEL)
            if btn:
                username = (await client.get_me()).username
                param = message.command[1] if len(message.command) > 1 else "true"
                btn.append([
                    InlineKeyboardButton("♻️ ʀᴇғʀᴇsʜ ♻️", url=f"https://t.me/{username}?start={param}")
                ])
                
                await message.reply_photo(
                    photo="https://i.postimg.cc/7Zpf9s1C/IMG-20250514-223544-954.jpg",
                    caption=(
                        f"<b>👋 Hello {message.from_user.mention},</b>\n\n"
                        "ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜꜱᴇ ᴍᴇ, ʏᴏᴜ ᴍᴜꜱᴛ ꜰɪʀꜱᴛ ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ.\n"
                        "ᴄʟɪᴄᴋ ᴏɴ \"✇ ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ ✇\" ʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴛᴀᴘ \"ʀᴇǫᴜᴇꜱᴛ ᴛᴏ ᴊᴏɪɴ\".\n"
                        "ᴀꜰᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴏɴ \"ʀᴇғʀᴇsʜ\" ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ."
                    ),
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
        except Exception as e:
            logger.error(f"[START ERROR] {e}")

    # ✅ Save user to DB
    await tasks.update_one(
        {"user_id": message.from_user.id},
        {"$setOnInsert": {"user_id": message.from_user.id}},
        upsert=True
    )

    # ✅ Send user log to log channel
    try:
        bd_time = datetime.now(timezone("Asia/Dhaka")).strftime("%d %B, %Y - %I:%M %p")
        mention_user = message.from_user.mention if message.from_user.username else message.from_user.first_name
        log_text = (
            "<b>📗 New User Joined! SCREENSHOT 🖼️</b>\n\n"
            f"👤 <b>Name:</b> {message.from_user.first_name}\n"
            f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
            f"🔗 <b>Mention:</b> {mention_user}\n"
            f"🕰️ <b>Joined At:</b> {bd_time}"
        )

        await client.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=log_text
        )
    except Exception as e:
        logger.error(f"[User Log Error] {e}")

    # ✅ Send welcome message (Original message preserved)
    await message.reply_photo(
        photo="https://i.postimg.cc/y8h4mNXn/file-0000000088e461f88f1ee0cb5eb1db66.png",
        caption=(
            f"👋 ʜᴇʏ {message.from_user.mention},\n\n"
            "I’ᴍ ᴀ ʟɪɢʜᴛᴡᴇɪɢʜᴛ ʏᴇᴛ ᴘᴏᴡᴇʀꜰᴜʟ ʙᴏᴛ — ᴅᴇꜱɪɢɴᴇᴅ ᴛᴏ ꜱᴍᴀʀᴛʟʏ ɢᴇɴᴇʀᴀᴛᴇ ꜱᴄʀᴇᴇɴꜱʜᴏᴛꜱ ꜰʀᴏᴍ ᴀɴʏ ᴠɪᴅᴇᴏ, ᴅᴏᴄᴜᴍᴇɴᴛ, ᴏʀ ᴘᴅꜰ.\n\n"
            "🎬 ꜱᴇɴᴅ ᴀɴʏ <b>ᴠɪᴅᴇᴏ</b>, <b>ᴅᴏᴄᴜᴍᴇɴᴛ</b>, ᴏʀ <b>ᴘᴅꜰ</b> — ᴀɴᴅ ɪ'ʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ɢᴇɴᴇʀᴀᴛᴇ <b>15 ᴘʀᴇᴠɪᴇᴡ ꜱᴄʀᴇᴇɴꜱʜᴏᴛꜱ</b> ꜰʀᴏᴍ ɪᴛ!\n\n"
            "📥 ɴᴏ ᴄᴏᴍᴍᴀɴᴅꜱ, ɴᴏ ᴄᴏɴꜰᴜꜱɪᴏɴ — ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴀ ꜰɪʟᴇ ᴀɴᴅ ᴡᴀᴛᴄʜ ᴍᴇ ɪɴ ᴀᴄᴛɪᴏɴ.\n\n"
            "<blockquote>🌿 ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ: <a href='https://t.me/PrimeXBots'>@ᴘʀɪᴍᴇXʙᴏᴛꜱ</a></blockquote>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💬 ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ 💬", url="https://t.me/Prime_Support_Group"),
                InlineKeyboardButton("〄 ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ 〄", url="https://t.me/PrimeXBots")
            ],
            [
                InlineKeyboardButton("✧ ᴄʀᴇᴀᴛᴏʀ ✧", url="https://t.me/Prime_Nayem")
            ]
        ])
    )

@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    await message.reply_text(
        "📌 <b>ʜᴏᴡ ᴛᴏ ᴜꜱᴇ ᴍᴇ?</b>\n\n"
        "📤 ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴀɴʏ <b>ᴠɪᴅᴇᴏ</b>, <b>ᴅᴏᴄᴜᴍᴇɴᴛ</b>, ᴏʀ <b>ᴘᴅꜰ ꜰɪʟᴇ</b>.\n"
        "🔍 ɪ’ʟʟ ᴀɴᴀʟʏᴢᴇ ɪᴛ ᴀɴᴅ ɢᴇɴᴇʀᴀᴛᴇ <b>15 ʀᴀɴᴅᴏᴍ ꜱᴄʀᴇᴇɴꜱʜᴏᴛꜱ</b> ꜰʀᴏᴍ ᴛʜᴇ ᴄᴏɴᴛᴇɴᴛ.\n"
        "✅ ᴍᴀᴋᴇ ꜱᴜʀᴇ ʏᴏᴜ’ʀᴇ ꜱᴜʙꜱᴄʀɪʙᴇᴅ ᴛᴏ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜꜱᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ.\n\n"
        "💡 ꜰᴇᴇʟ ꜰʀᴇᴇ ᴛᴏ ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ ꜱᴜᴘᴘᴏʀᴛ ɪꜰ ʏᴏᴜ ɴᴇᴇᴅ ᴀɴʏ ʜᴇʟᴘ!",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("💬 ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ 💬", url="https://t.me/Prime_Support_Group")]]
        )
    )

@app.on_message(filters.command("cancel"))
async def cancel_handler(client, message: Message):
    user_id = message.from_user.id
    result = await tasks.update_many(
        {"user_id": user_id, "status": {"$in": ["pending", "processing"]}},
        {"$set": {"status": "cancelled"}}
    )
    if result.modified_count > 0:
        await message.reply_text(f"✅ Cancelled {result.modified_count} task(s).")
    else:
        await message.reply_text("ℹ️ No active tasks to cancel.")

@app.on_callback_query(filters.regex("cancel_task"))
async def cancel_callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    result = await tasks.update_many(
        {"user_id": user_id, "status": {"$in": ["pending", "processing"]}},
        {"$set": {"status": "cancelled"}}
    )
    await callback_query.answer("✅ Task(s) cancelled.", show_alert=True)
    await callback_query.message.edit_text("✅ Task cancelled by user.")

@app.on_message(filters.command("status"))
async def status_handler(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ You are not allowed to use this command! Only the bot owner or admin can access it.")

    total_users = await tasks.distinct("user_id")
    pending = await tasks.count_documents({"status": "pending"})
    processing = await tasks.count_documents({"status": "processing"})
    done = await tasks.count_documents({"status": "done"})
    cancelled = await tasks.count_documents({"status": "cancelled"})
    failed = await tasks.count_documents({"status": "failed"})

    text = f"""📊 **Bot Status**
👥 Total Users: `{len(total_users)}`
⏳ Pending: `{pending}`
⚙️ Processing: `{processing}`
✅ Done: `{done}`
❌ Cancelled: `{cancelled}`
🚫 Failed: `{failed}`
"""
    await message.reply_text(text)

@app.on_message(filters.command("broadcast"))
async def broadcast_handler(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ You are not allowed to use this command! Only the bot owner or admin can access it.")

    if not message.reply_to_message:
        return await message.reply_text("❗ Please reply to a message you want to broadcast.")

    msg = message.reply_to_message
    user_ids = await tasks.distinct("user_id")

    sent = 0
    for uid in user_ids:
        try:
            await client.copy_message(uid, msg.chat.id, msg.id)
            sent += 1
        except Exception:
            # User blocked bot, etc.
            continue
    await message.reply_text(f"✅ Broadcast sent to {sent} users.")
    
@app.on_message(filters.document | filters.video)
async def file_handler(client, message: Message):
    if AUTH_CHANNEL:
        try:
            btn = await is_subscribed(client, message, AUTH_CHANNEL)
            if btn:
                await message.reply_photo(
                    photo="https://i.postimg.cc/7Zpf9s1C/IMG-20250514-223544-954.jpg",
                    caption=(
                        f"<b>👋 Hello {message.from_user.mention},\n\n"
                        "ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜꜱᴇ ᴍᴇ, ʏᴏᴜ ᴍᴜꜱᴛ ꜰɪʀꜱᴛ ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ.\n"
                        "ᴄʟɪᴄᴋ ᴏɴ \"✇ ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ ✇\" ʙᴜᴛᴛᴏɴ ᴀɴᴅ ᴛᴀᴘ \"ʀᴇǫᴜᴇꜱᴛ ᴛᴏ ᴊᴏɪɴ\".\n"
                        "✅ ᴏɴᴄᴇ ʏᴏᴜ'ᴠᴇ ᴊᴏɪɴᴇᴅ, sᴇɴᴅ ʏᴏᴜʀ ꜰɪʟᴇ ᴀɢᴀɪɴ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ.</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
        except Exception as e:
            logger.error(f"[File Handler Auth Error] {e}")
            
    user_id = message.from_user.id
    await tasks.update_one({"user_id": user_id}, {"$setOnInsert": {"user_id": user_id}}, upsert=True)

    existing_task = await tasks.find_one({"user_id": user_id, "status": {"$in": ["pending", "processing"]}})
    if existing_task:
        await message.reply_text("⚠️ You already have a task in progress. Please wait or use /cancel.")
        return

    file = message.document or message.video
    
    # Restored Original Queue Message
    reply = await message.reply_text(
        "📥 ǫᴜᴇᴜᴇᴅ ꜰᴏʀ ᴘʀᴏᴄᴇꜱꜱɪɴɢ...\n\n🔄 ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ, ᴍᴜʟᴛɪᴘʟᴇ ᴜꜱᴇʀꜱ ᴀʀᴇ ꜱᴇɴᴅɪɴɢ ꜰɪʟᴇꜱ ꜰᴏʀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ.\n🔄 ᴏɴᴇ ʙʏ ᴏɴᴇ, ᴍᴀɴʏ ꜰɪʟᴇꜱ ᴀʀᴇ ʙᴇɪɴɢ ᴘʀᴏᴄᴇꜱꜱᴇᴅ.\nʏᴏᴜʀ ꜰɪʟᴇ ɪꜱ ɴᴏᴡ ɪɴ ǫᴜᴇᴜᴇ.\n\n⏳ ᴘʟᴇᴀꜱᴇ ʙᴇ ᴘᴀᴛɪᴇɴᴛ — ɴᴏ ᴀᴄᴛɪᴏɴ ɴᴇᴇᴅᴇᴅ ꜰʀᴏᴍ ʏᴏᴜ.\n\n🔐 ᴅᴏɴ'ᴛ ᴡᴏʀʀʏ, ʏᴏᴜʀ ꜰɪʟᴇ ɪꜱ ɪɴ ꜱᴀꜰᴇ ʜᴀɴᴅꜱ.\nɪᴛ ᴡɪʟʟ ʙᴇ ᴘʀᴏᴄᴇꜱꜱᴇᴅ ᴀꜱ ꜱᴏᴏɴ ᴀꜱ ʏᴏᴜʀ ᴛᴜʀɴ ᴄᴏᴍᴇꜱ.\n\n📸 ᴀꜱ ꜱᴏᴏɴ ᴀꜱ ʏᴏᴜʀ ꜱʟᴏᴛ ɪꜱ ʀᴇᴀᴄʜᴇᴅ,\nᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ɢᴇɴᴇʀᴀᴛᴇ ᴀɴᴅ ᴅᴇʟɪᴠᴇʀ ʏᴏᴜʀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛꜱ.\n\n💤 ꜱɪᴛ ʙᴀᴄᴋ, ʀᴇʟᴀx — ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴡᴏʀᴋɪɴɢ ꜰᴏʀ ʏᴏᴜ.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")]]
        )
    )

    await tasks.insert_one({
        "user_id": user_id,
        "chat_id": message.chat.id,
        "message_id": message.id,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "file_info": {
            "file_id": file.file_id,
            "file_name": getattr(file, "file_name", None),
            "mime_type": file.mime_type,
            "file_size": file.file_size,
        },
        "reply_id": reply.id
    })

async def worker():
    while True:
        task = await tasks.find_one_and_update(
            {"status": "pending"},
            {"$set": {"status": "processing"}}
        )

        if not task:
            await asyncio.sleep(2)
            continue
        
        file_path = None # Initialize file_path for cleanup
        
        try:
            # If the user cancelled the task in the meantime
            latest_task = await tasks.find_one({"_id": task["_id"]})
            if latest_task["status"] == "cancelled":
                logger.info(f"Task {task['_id']} skipped because it was cancelled.")
                continue

            chat_id = task["chat_id"]
            message_id = task["message_id"]
            reply_id = task["reply_id"]
            
            try:
                message = await app.get_messages(chat_id, message_id)
                reply = await app.get_messages(chat_id, reply_id)
            except Exception as e:
                logger.warning(f"Message/Reply not found for task {task['_id']}. Error: {e}")
                await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "failed", "error": "Message/Reply deleted"}})
                continue

            # Check for cancellation again right before long-running download
            latest_task = await tasks.find_one({"_id": task["_id"]})
            if latest_task["status"] == "cancelled":
                logger.info(f"Task {task['_id']} cancelled during processing check.")
                continue

            file = message.document or message.video
            
            # Download file
            file_path = await app.download_media(file, progress=progress_bar, progress_args=(reply,))
            
            if not file_path:
                await reply.edit_text("❌ Failed to download the file.")
                await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "failed", "error": "Download failed"}})
                continue

            mime_type, _ = mimetypes.guess_type(file_path)
            filename = extract_filename(file) or os.path.basename(file_path)
            await reply.edit_text(f"📄 Processing `{filename}`...")

            screenshots = []
            if mime_type:
                if mime_type.startswith("application/"):
                    # Assuming screenshot_document handles PDFs and other docs
                    screenshots = await asyncio.get_event_loop().run_in_executor(None, screenshot_document, file_path)
                elif mime_type.startswith("video/"):
                    screenshots = await asyncio.get_event_loop().run_in_executor(None, screenshot_video, file_path)

            if not screenshots:
                await reply.edit_text("❌ Could not generate screenshots. (File type not supported or corrupted)")
                await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "failed", "error": "Screenshot generation failed"}})
                continue

            await reply.edit_text("📤 Uploading screenshots...")
            
            # Upload Screenshots
            for ss in screenshots:
                await app.send_photo(chat_id, ss)
                os.remove(ss) # Remove generated screenshot file immediately

            await reply.delete()
            # Original message delete is optional, but kept as per your original logic
            await message.delete() 
            await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "done"}})

        except Exception as e:
            logger.error(f"Worker Error for task {task['_id']}: {e}")
            await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "failed", "error": str(e)}})
            
        finally:
            # CRITICAL: Clean up downloaded source file
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up source file: {file_path}")
            
            # Sleep short if task processed, long if no task found (handled at the beginning of loop)


# --- Koyeb Health Check ---
async def handle(request):
    return web.Response(text="Bot is Alive!")

async def run_web():
    app_web = web.Application()
    app_web.router.add_get("/", handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

# Final run
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    # New: Check DB connection before starting workers
    loop.run_until_complete(check_db_connection()) 
    
    loop.create_task(run_web())

    # Run multiple workers for concurrent user processing
    for i in range(5):  # Worker count: 5
        loop.create_task(worker())
        logger.info(f"Worker {i+1} started.")

    app.run()

#--- END OF FILE bot.py ---
