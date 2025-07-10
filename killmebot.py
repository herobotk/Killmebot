import os
import re
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from humanize import naturalsize

# ================== Config ==================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================== Health Check Server ==================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is alive!')

def run_http_server():
    server = HTTPServer(("", 8080), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# ================== Title Shortener ==================
def shorten_title(filename):
    title_map = {
        "Jawan": "JW23",
        "Pathaan": "PTN23",
        "Animal": "ANML23",
        "Fighter": "FGTR24",
        "Gadar": "GDR22",
        # add more as needed
    }
    for full, short in title_map.items():
        filename = re.sub(fr'\b{re.escape(full)}\b', short, filename, flags=re.IGNORECASE)
    return filename

# ================== Cleaner ==================
def clean_filename(filename):
    keep_username = "@movie_talk_backup"
    filename = filename.replace(keep_username, "___KEEP__USERNAME___")

    # Title shortening
    filename = shorten_title(filename)

    # Remove mentions, links, domains
    filename = re.sub(r'@\w+', '', filename)
    filename = re.sub(r'https?://\S+|www\.\S+|\S+\.(com|in|net|org|me|info)', '', filename)
    filename = re.sub(r't\.me/\S+', '', filename)

    # Remove unwanted characters but keep _ . - ( ) letters and numbers
    filename = re.sub(r'[^\w\s.\-()_]', '', filename)
    filename = re.sub(r'\s{2,}', ' ', filename).strip()

    filename = filename.replace("___KEEP__USERNAME___", keep_username)
    return filename

# ================== Caption Builder ==================
def generate_caption(file_name, file_size):
    cleaned_name = clean_filename(file_name)
    return f"""{cleaned_name}
⚙️ 𝚂𝚒𝚣𝚎 ~ [{file_size}]
⚜️ 𝙿𝚘𝚜𝚝 𝚋𝚢 ~ 𝐌𝐎𝐕𝐈𝐄 𝐓𝐀𝐋𝐊

⚡𝖩𝗈𝗂𝗇 Us ~ ❤️ 
➦『 @movie_talk_backup 』"""

def log(msg):
    print(f"[KILLBOT] {msg}", flush=True)

# ================== Bot Setup ==================
bot = Client("kill_me_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================== Commands (PM Only) ==================
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(_, message: Message):
    await message.reply("👋 Bot is alive! Mentions cleaner + auto caption is running.")

@bot.on_message(filters.private & filters.command("help"))
async def help_cmd(_, message: Message):
    await message.reply_text(
        "📌 Bot Commands:\n"
        "/start – Start the bot\n"
        "/help – Show this help menu\n\n"
        "📬 Need Help? [𝐇𝐞𝐥𝐩 𝐨𝐫 𝐑𝐞𝐩𝐨𝐫𝐭 𝐛𝐨𝐭](http://t.me/Fedbk_rep_bot)",
        disable_web_page_preview=False
    )
    
# ================== Clean text messages ==================
@bot.on_message(filters.channel & ~filters.me & filters.text)
async def clean_text_msg(_, message: Message):
    cleaned = clean_filename(message.text)
    if cleaned != message.text:
        try:
            await message.edit_text(cleaned)
            log("Text edited.")
        except Exception as e:
            log(f"Text edit failed: {e}")

# ================== Clean media captions ==================
@bot.on_message(filters.channel & ~filters.me & (filters.video | filters.document | filters.audio | filters.photo))
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
    except FloodWait as e:
        log(f"FloodWait: Sleeping for {e.value} seconds...")
        await asyncio.sleep(e.value)
        try:
            await message.copy(chat_id=message.chat.id, caption=caption)
            await message.delete()
            log("Media reposted after wait.")
        except Exception as e2:
            log(f"Retry failed: {e2}")
    except Exception as e:
        log(f"Failed to update media: {e}")

# ================== Run ==================
bot.run()
