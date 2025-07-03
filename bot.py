import os
import asyncio
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from utils import screenshot_video, screenshot_document, extract_filename, progress_bar
from force_sub import is_subscribed, FSUB_CHANNEL, get_channel_name
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Bot credentials from environment variables
api_id = int(os.getenv("API_ID", "12345"))
api_hash = os.getenv("API_HASH", "your_api_hash")
bot_token = os.getenv("BOT_TOKEN", "your_bot_token")
mongo_url = os.getenv("MONGO_DB_URI", "mongodb://localhost:27017")

# Pyrogram client init
app = Client("advanced_screenshot_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# MongoDB Setup
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client["screenshot_bot"]
tasks = db["tasks"]

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text(
        "👋 Welcome! Send a video or document (PDF etc) and I'll generate 15 screenshots!\n\nJoin our update channel to use this bot.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FSUB_CHANNEL}")]]
        )
    )

@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    await message.reply_text(
        "❓ Just send a video or document (PDF, etc).\n✅ Make sure you're subscribed to our channel.\nI'll generate 15 screenshots for you!"
    )

@app.on_message(filters.command("cancel"))
async def cancel_handler(client, message: Message):
    user_id = message.from_user.id
    result = await tasks.delete_many({"user_id": user_id, "status": "pending"})
    if result.deleted_count > 0:
        await message.reply_text(f"❌ {result.deleted_count} pending task(s) cancelled.")
    else:
        await message.reply_text("ℹ️ No pending tasks found to cancel.")

@app.on_message(filters.document | filters.video)
async def file_handler(client, message: Message):
    user_id = message.from_user.id
    existing_task = await tasks.find_one({"user_id": user_id, "status": {"$in": ["pending", "processing"]}})

    if existing_task:
        await message.reply_text("⚠️ You already have a task in progress. Please wait for it to finish or use /cancel to cancel it.")
        return

    file = message.document or message.video
    reply = await message.reply_text("📥 Queued for processing...")

    await tasks.insert_one({
        "user_id": user_id,
        "chat_id": message.chat.id,
        "message_id": message.id,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "file": file,
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

        try:
            chat_id = task["chat_id"]
            message_id = task["message_id"]
            reply_id = task["reply_id"]
            user_file = task["file"]

            message = await app.get_messages(chat_id, message_id)
            reply = await app.get_messages(chat_id, reply_id)

            file = message.document or message.video
            file_path = await app.download_media(
                file,
                progress=progress_bar,
                progress_args=(reply,)
            )

            if not file_path:
                await reply.edit("❌ Failed to download the file.")
                await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "failed"}})
                continue

            mime_type, _ = mimetypes.guess_type(file_path)
            filename = extract_filename(file) or os.path.basename(file_path)
            await reply.edit_text(f"📄 Processing `{filename}`...")

            screenshots = []
            if mime_type:
                if mime_type.startswith("application/"):
                    screenshots = await asyncio.get_event_loop().run_in_executor(None, screenshot_document, file_path)
                elif mime_type.startswith("video/"):
                    screenshots = await asyncio.get_event_loop().run_in_executor(None, screenshot_video, file_path)

            if not screenshots:
                await reply.edit("❌ Could not generate screenshots.")
                await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "failed"}})
                continue

            await reply.edit("📤 Uploading screenshots...")
            for ss in screenshots:
                await app.send_photo(chat_id, ss)

            await reply.delete()
            await message.delete()

            await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "done"}})

        except Exception as e:
            print("Worker Error:", e)
            await tasks.update_one({"_id": task["_id"]}, {"$set": {"status": "failed", "error": str(e)}})

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
    loop.create_task(run_web())
    loop.create_task(worker())
    app.run()


