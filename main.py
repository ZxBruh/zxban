import time
import json
import os
import io
import sys
import subprocess
from contextlib import redirect_stdout
from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityCustomEmoji

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "info_template": "🛡️ **Zxban Status**",
            "ping_template": "🏓 **Pong!** `{time}` ms",
            "help_template": "**📜 Список команд:**\n`!инфо` — статус\n`!пинг` — задержка\n`!хелп` — команды\n`!кфг` — настройки\n`!е` — python\n`!терминал` — консоль\n`!апдейт` — обновить",
            "prefix": "!"
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

config_data = load_config()
PREFIX = config_data.get("prefix", "!")
client = TelegramClient('zxban_session', API_ID, API_HASH)

async def edit_with_emoji(event, text, emoji_id):
    await event.edit(text, formatting_entities=[
        MessageEntityCustomEmoji(offset=0, length=2, document_id=emoji_id)
    ])

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}инфо'))
async def info(event):
    cfg = load_config()
    await edit_with_emoji(event, "🛡️ " + cfg.get("info_template"), 5431682333653110201)

@client.on(events.NewMessage(
