import os
import asyncio
import mimetypes
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from utils import screenshot_video, screenshot_document, extract_filename, progress_bar

# aiohttp for health check
from aiohttp import web

api_id = int(os.getenv("API_ID", "12345"))
api_hash = os.getenv("API_HASH", "your_api_hash")
bot_token = os.getenv("BOT_TOKEN", "your_bot_token")

app = Client("advanced_screenshot_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
user_locks = {}

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text("👋 Welcome! Send a video or document and I'll give you 15 screenshots!")

@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    await message.reply_text("❓ Just send a video or document file.\nI'll generate 15 screenshots for you!")

@app.on_message(filters.document | filters.video)
async def file_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()

    async with user_locks[user_id]:
        file = message.document or message.video
        reply = await message.reply_text("📥 Downloading file...")
        file_path = await client.download_media(file, progress=progress_bar, progress_args=(reply, file.file_size))
        if not file_path:
            return await reply.edit("❌ Failed to download the file.")

        mime_type, _ = mimetypes.guess_type(file_path)
        filename = extract_filename(file)
        await reply.edit_text(f"📄 Processing `{filename}`...")

        if mime_type.startswith("application/"):
            screenshots = await asyncio.get_event_loop().run_in_executor(None, screenshot_document, file_path)
        elif mime_type.startswith("video/"):
            screenshots = await asyncio.get_event_loop().run_in_executor(None, screenshot_video, file_path)
        else:
            await reply.edit("❌ Unsupported file type.")
            os.remove(file_path)
            return

        os.remove(file_path)

        if screenshots:
            await reply.edit("📤 Uploading screenshots...")
            for ss in screenshots:
                await client.send_photo(message.chat.id, ss)
                os.remove(ss)
            await reply.delete()
            await message.delete()
        else:
            await reply.edit("❌ Failed to generate screenshots.")

# ✅ HEALTH CHECK SERVER ON PORT 8080
async def handle_health(request):
    return web.Response(text="OK")

async def run_health_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8080)
    await site.start()

# ✅ Run bot and health server together — FIXED
async def main():
    await app.start()
    await run_health_server()
    print("✅ Bot is running... Health server ready at http://localhost:8080/")
    await asyncio.Event().wait()  # ⬅️ Proper way to keep it alive

if __name__ == "__main__":
    asyncio.run(main())
