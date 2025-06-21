import os
import re
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import Message
from humanize import naturalsize

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Health check server (port 8080)
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive!')

def run_http_server():
    server = HTTPServer(("", 8080), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# Bot setup
bot = Client("kill_me_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Pattern: all mentions except @movie_talk_backup and .com/.in/.link etc.
pattern = r"(@(?!movie_talk_backup)\w+|https?://\S+|www\.\S+|\S+\.(com|in|link|org|net))"

def clean_text(text):
    cleaned = re.sub(pattern, '', text)
    return re.sub(r'\s+', ' ', cleaned).strip()

def log(msg):
    print(f"[KILLBOT] {msg}", flush=True)

def auto_caption(file_name, file_size):
    return f"""{file_name}
⚙️ 𝚂𝚒𝚣𝚎 ~ [{file_size}]
⚜️ 𝙿𝚘𝚜𝚝 𝚋𝚢 ~ 𝐌𝐎𝐕𝐈𝐄 𝐓𝐀𝐋𝐊

⚡𝖩𝗈𝗂𝗇 Us ~ ❤️ 
➦『 @movie_talk_backup 』"""

# Commands
@bot.on_message(filters.private & filters.command("start"))
async def start_command(client, message: Message):
    await message.reply("👋 Bot is alive! I clean @mentions, .com links & add captions.")

@bot.on_message(filters.private & filters.command("help"))
async def help_command(client, message: Message):
    await message.reply(
        """📌 *Kill Me Bot Help:*
- Removes unwanted @mentions (except @movie_talk_backup)
- Removes .com, http links from messages
- Adds auto captions to media files
- Works with text, videos, docs, photos
- Instant process (no delay)
""",
        quote=True,
        parse_mode="Markdown"
    )

# Clean text posts in channel
@bot.on_message(filters.channel & filters.text)
async def clean_text_messages(client, message: Message):
    log(f"Received text: {message.text}")
    cleaned = clean_text(message.text)
    log(f"Cleaned text: {cleaned}")
    if cleaned != message.text:
        try:
            await message.edit_text(cleaned)
            log("Text message edited successfully.")
        except Exception as e:
            log(f"Edit text failed: {e}")

# Clean captions or add auto-caption to media
@bot.on_message(filters.channel & (filters.video | filters.document | filters.audio | filters.photo))
async def clean_media_caption(client, message: Message):
    media = message.document or message.video or message.audio
    original_caption = message.caption or ""

    if media and media.file_name:
        file_name = media.file_name
        file_size = naturalsize(media.file_size)
        caption = auto_caption(file_name, file_size)
        log(f"Auto caption generated for {file_name} [{file_size}]")
    else:
        caption = clean_text(original_caption)
        log(f"Cleaned original caption: {caption}")

    if caption != original_caption:
        try:
            await message.copy(chat_id=message.chat.id, caption=caption)
            await message.delete()
            log("Media copied with cleaned or auto caption.")
        except Exception as e:
            log(f"Caption update failed: {e}")

# Run bot
bot.run()
