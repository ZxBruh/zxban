import time, json, os, sys, subprocess, importlib, random, string
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji

# --- КОНФИГУРАЦИЯ ---
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'
MODULES_DIR = 'modules'

# Укажи здесь юзернейм своего старого бота (без @), чтобы он не менялся
DEFAULT_BOT_USERNAME = "твой_старый_бот_username" 

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)

def load_config():
    # Если файла нет, создаем с дефолтным (старым) ботом
    default = {
        "prefix": "!",
        "bot_token": "",
        "bot_username": DEFAULT_BOT_USERNAME,
        "info_template": "🛡️ **Zxban Status: Online**",
        "ping_template": "⚡ **Pong!** `{time}` ms"
    }
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
        return default
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        current = json.load(f)
    
    # Если в старом конфиге не было bot_username, ставим наш стандартный
    if "bot_username" not in current or current["bot_username"].startswith("zxban_"):
        current["bot_username"] = DEFAULT_BOT_USERNAME
        
    # Проверка остальных ключей
    for k, v in default.items():
        if k not in current: current[k] = v
            
    return current

cfg = load_config()
client = TelegramClient('zxban_session', API_ID, API_HASH)
bot_client = None

# Запуск бота-помощника
if cfg.get("bot_token"):
    try:
        # Используем существующий токен
        bot_client = TelegramClient('zxban_bot', API_ID, API_HASH).start(bot_token=cfg["bot_token"])
    except Exception as e:
        print(f"Ошибка запуска бота: {e}")

loaded_modules = {}

@client.on(events.NewMessage(outgoing=True))
async def main_handler(event):
    global cfg
    prefix = cfg.get("prefix", "!")
    if not event.raw_text.startswith(prefix): return
    args = event.raw_text[len(prefix):].split()
    if not args: return
    cmd = args[0].lower()

    if cmd == "кфг":
        if not bot_client:
            await event.edit(f"⚠️ **Нужен старый бот!**\nУбедись, что токен от `@{cfg['bot_username']}` привязан.\nВведи: `!set_token ТОКЕН`")
            return
        
        try:
            # Отправка через старого бота
            await bot_client.send_message(event.chat_id, "⚙️ **Настройки Zxban**", buttons=[
                [Button.inline("📦 Встроенные", data="mods_int")],
                [Button.inline("🌐 Внешние", data="mods_ext")]
            ])
            await event.delete()
        except Exception:
            await event.edit(f"❌ **Бот не видит тебя!**\nПерейди в `@{cfg['bot_username']}` и нажми СТАРТ.")

    elif cmd == "set_token":
        if len(args) > 1:
            cfg['bot_token'] = args[1]
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=4)
            await event.edit("✅ Токен обновлен! Перезагрузка...")
            os.execl(sys.executable, sys.executable, *sys.argv)

    elif cmd == "пинг":
        start = time.time()
        await event.edit("🚀")
        ms = round((time.time() - start) * 1000)
        await event.edit(f"⚡ {cfg['ping_template'].replace('{time}', str(ms))}", 
                         formatting_entities=[MessageEntityCustomEmoji(offset=0, length=2, document_id=5447103212130101411)])

    elif cmd == "апдейт":
        await event.edit("🔄 **Обновление...**")
        subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE).communicate()
        os.execl(sys.executable, sys.executable, *sys.argv)

if bot_client:
    @bot_client.on(events.CallbackQuery)
    async def cb_handler(event):
        if event.data == b"mods_int":
            await event.edit("🛠 Core, Loader, Net", buttons=[Button.inline("⬅️ Назад", data="back")])
        elif event.data == b"back":
            await event.edit("⚙️ **Настройки Zxban**", buttons=[[Button.inline("📦 Встроенные", data="mods_int")]])

async def main():
    await client.start()
    print(f"Zxban запущен! Бот-помощник: @{cfg['bot_username']}")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
