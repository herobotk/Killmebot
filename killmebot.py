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

# ================== Alphabet Map ==================
alphabet_map = {
    'A': '@', 'B': 'B', 'C': '©', 'D': 'Ð', 'E': 'Ɇ', 'F': '₣', 'G': 'Ǥ',
    'H': '#', 'I': '!', 'J': 'ʝ', 'K': 'Ҝ', 'L': 'Ↄ', 'M': '♏', 'N': '₪',
    'O': '()', 'P': '₱', 'Q': 'Ǫ', 'R': '®', 'S': '$', 'T': '†', 'U': 'Ü',
    'V': '√', 'W': 'Ш', 'X': '✘', 'Y': '¥', 'Z': '乙'
}

def transform_alphabet(text: str) -> str:
    result = ""
    for char in text:
        if char.upper() in alphabet_map:
            result += alphabet_map[char.upper()]
        else:
            result += char
    return result

# ================== Caption Builder ==================
def generate_caption(file_name, file_size):
    transformed = transform_alphabet(file_name)
    return f"""{transformed}
⚙️ 𝚂𝚒𝚣𝚎 ~ [{file_size}]
⚜️ 𝙿𝚘𝚜𝚝 𝚋𝚢 ~ 𝐌𝐎𝐕𝐈𝐄 𝐓𝐀𝐋𝐊

⚡𝖩𝗈𝗂𝗇 Us ~ ❤️ 
➦『 @movie_talk_backup 』"""

def log(msg):
    print(f"[KILLBOT] {msg}", flush=True)

# ================== Bot Setup ==================
bot = Client("kill_me_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================== Commands ==================
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(_, message: Message):
    await message.reply("👋 Bot is alive! Alphabet transformer is running.")

@bot.on_message(filters.private & filters.command("help"))
async def help_cmd(_, message: Message):
    await message.reply_text(
        "📌 Bot Commands:\n"
        "/start – Start the bot\n"
        "/help – Show this help menu\n\n"
        "📬 Need Help? [𝐇𝐞𝐥𝐩 𝐨𝐫 𝐑𝐞𝐩𝐨𝐫𝐭 𝐛𝐨𝐭](http://t.me/Fedbk_rep_bot)",
        disable_web_page_preview=False
    )

# ================== Caption Transformer ==================
@bot.on_message(filters.channel & ~filters.me & (filters.video | filters.document | filters.audio))
async def transform_caption(_, message: Message):
    media = message.document or message.video or message.audio
    if not media or not media.file_name:
        return

    file_name = media.file_name
    file_size = naturalsize(media.file_size)
    caption = generate_caption(file_name, file_size)

    try:
        await message.copy(chat_id=message.chat.id, caption=caption)
        await message.delete()
        log(f"✅ Caption transformed and reposted: {file_name}")
    except FloodWait as e:
        log(f"⏳ FloodWait: Waiting for {e.value} seconds...")
        await asyncio.sleep(e.value)
        try:
            await message.copy(chat_id=message.chat.id, caption=caption)
            await message.delete()
            log("✅ Reposted after wait.")
        except Exception as err:
            log(f"❌ Retry failed: {err}")
    except Exception as e:
        log(f"❌ Failed to repost: {e}")

# ================== Run ==================
bot.run()
