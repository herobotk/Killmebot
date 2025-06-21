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

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive!')

def run_http_server():
    server = HTTPServer(("", 8080), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

bot = Client("kill_me_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

pattern = r"(@(?!movie_talk_backup)\w+|https?://\S+|www\.\S+|\S+\.com)"

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
- Waits 5 seconds for media cleanup
""",
        quote=True,
        parse_mode="Markdown"
    )

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

@bot.on_message(filters.channel & (filters.video | filters.document | filters.audio | filters.photo))
async def clean_media_caption(client, message: Message):
    await asyncio.sleep(5)
    media = message.document or message.video or message.audio
    if media:
        file_name = media.file_name or "Unknown"
        file_size = naturalsize(media.file_size)
        caption = auto_caption(file_name, file_size)
        log(f"Auto caption generated for {file_name} [{file_size}]")

        try:
            await message.copy(chat_id=message.chat.id, caption=caption)
            await message.delete()
            log("Media copied with auto caption.")
        except Exception as e:
            log(f"Media copy failed: {e}")
    elif message.caption:
        cleaned = clean_text(message.caption)
        log(f"Cleaned existing caption: {cleaned}")
        if cleaned != message.caption:
            try:
                await message.copy(chat_id=message.chat.id, caption=cleaned)
                await message.delete()
                log("Media caption cleaned.")
            except Exception as e:
                log(f"Caption clean failed: {e}")

bot.run()
