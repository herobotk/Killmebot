import os
import re
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import Message
from humanize import naturalsize

# ====== Config from Environment ======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ====== Health Check Server (Koyeb etc.) ======
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive!')

def run_http_server():
    server = HTTPServer(("", 8080), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# ====== Mention Killer Logic ======
def clean_filename(filename):
    keep_username = "@movie_talk_backup"
    filename = filename.replace(keep_username, "___KEEP__USERNAME___")
    filename = re.sub(r'@\w+', '', filename)
    filename = re.sub(r'https?://\S+|www\.\S+|\S+\.(com|in|net|org|me|info)', '', filename)
    filename = re.sub(r't\.me/\S+', '', filename)
    filename = re.sub(r'[^\w\s.\-()]', '', filename)
    filename = re.sub(r'\s{2,}', ' ', filename).strip()
    filename = filename.replace("___KEEP__USERNAME___", keep_username)
    return filename

def generate_caption(file_name, file_size):
    cleaned_name = clean_filename(file_name)
    return f"""{cleaned_name}
⚙️ 𝚂𝚒𝚣𝚎 ~ [{file_size}]
⚜️ 𝙿𝚘𝚜𝚝 𝚋𝚢 ~ 𝐌𝐎𝐕𝐈𝐄 𝐓𝐀𝐋𝐊

⚡𝖩𝗈𝗂𝗇 Us ~ ❤️ 
➦『 @movie_talk_backup 』"""

def log(msg):
    print(f"[KILLBOT] {msg}", flush=True)

# ====== Bot Setup ======
bot = Client("kill_me_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ====== Commands ======
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(_, message: Message):
    await message.reply("👋 Bot is alive! Mentions cleaner + auto caption is running.")

@bot.on_message(filters.private & filters.command("help"))
async def help_cmd(_, message: Message):
    await message.reply(
        """📌 *Kill Me Bot Help:*
- Cleans unwanted @mentions, t.me, .com, etc.
- Keeps only @movie_talk_backup
- Adds auto caption on media
- Works with video, document, audio, photo
- Instant process (no delay)
""",
        parse_mode="Markdown"
    )

# ====== Clean text in channel ======
@bot.on_message(filters.channel & filters.text)
async def clean_text_msg(_, message: Message):
    cleaned = clean_filename(message.text)
    if cleaned != message.text:
        try:
            await message.edit_text(cleaned)
            log("Text edited.")
        except Exception as e:
            log(f"Text edit failed: {e}")

# ====== Clean media caption / apply auto caption ======
@bot.on_message(filters.channel & (filters.video | filters.document | filters.audio | filters.photo))
async def clean_caption(_, message: Message):
    media = message.document or message.video or message.audio
    original_caption = message.caption or ""

    if media and media.file_name:
        file_name = media.file_name
        file_size = naturalsize(media.file_size)
        caption = generate_caption(file_name, file_size)
        log(f"Auto caption ready for: {file_name}")
    else:
        caption = clean_filename(original_caption)
        log("Original caption cleaned.")

    try:
        await message.copy(chat_id=message.chat.id, caption=caption)
        await message.delete()
        log("Media reposted with new caption.")
    except Exception as e:
        log(f"Failed to update media: {e}")

# ====== Run Bot ======
bot.run()
