import os
import asyncio
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from utils import screenshot_video, screenshot_document, extract_filename, progress_bar
from force_sub import is_subscribed, FSUB_CHANNEL, get_channel_name

from aiohttp import web  # For Koyeb Health Check

# Bot credentials from environment variables
api_id = int(os.getenv("API_ID", "12345"))
api_hash = os.getenv("API_HASH", "your_api_hash")
bot_token = os.getenv("BOT_TOKEN", "your_bot_token")

app = Client("advanced_screenshot_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
user_locks = {}

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

@app.on_message(filters.document | filters.video)
async def file_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()

    async with user_locks[user_id]:
        file = message.document or message.video
        reply = await message.reply_text("📥 Downloading file...")
        file_path = await client.download_media(
            file,
            progress=progress_bar,
            progress_args=(reply,)
        )
        if not file_path:
            return await reply.edit("❌ Failed to download the file.")

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
            return

        await reply.edit("📤 Uploading screenshots...")
        for ss in screenshots:
            await client.send_photo(message.chat.id, ss)

        await reply.delete()
        await message.delete()

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
    app.run()
    
