
import time, json, os, sys, subprocess, importlib, asyncio
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from telethon import TelegramClient, events, Button, functions, types

# --- КОНФИГУРАЦИЯ ---
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'
MODULES_DIR = 'modules'

def load_config():
    default = {"prefix": "!", "bot_token": "", "bot_username": ""}
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f: json.dump(default, f)
        return default
    return json.load(open(CONFIG_FILE))

cfg = load_config()
client = TelegramClient('zxban_session', API_ID, API_HASH)
loaded_modules = {}

# --- ФУНКЦИЯ АВТО-НАСТРОЙКИ BOTFATHER ---
async def setup_bot_inline(bot_username):
    print(f"🛠 Пытаюсь включить Inline Mode для @{bot_username} через BotFather...")
    async with client.conversation("@BotFather") as conv:
        await conv.send_message("/setinline")
        await asyncio.sleep(1)
        await conv.send_message(f"@{bot_username}")
        await asyncio.sleep(1)
        await conv.send_message("Zxban Mode") 
        print(f"✅ Инлайн режим для @{bot_username} должен быть включен!")

# --- ЗАГРУЗЧИК МОДУЛЕЙ ---
def load_modules():
    if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)
    for file in os.listdir(MODULES_DIR):
        if file.endswith(".py"):
            name = file[:-3]
            try:
                spec = importlib.util.spec_from_file_location(name, f"{MODULES_DIR}/{file}")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for attr in dir(mod):
                    handler = getattr(mod, attr)
                    if hasattr(handler, 'callback'): client.add_event_handler(handler)
                loaded_modules[name] = mod
            except Exception as e: print(f"❌ Ошибка в {name}: {e}")

@client.on(events.NewMessage(outgoing=True))
async def manager(event):
    global cfg
    text = event.raw_text
    prefix = cfg.get("prefix", "!")
    if not text.startswith(prefix): return
    
    cmd = text[len(prefix):].split()[0].lower()
    args = text.split()[1:]

    if cmd == "кфг":
        await event.delete()
        try:
            res = await client.inline_query(cfg['bot_username'], 'config_menu')
            await res[0].click(event.chat_id)
        except:
            await client.send_message("me", "❌ Ошибка: Инлайн-режим еще не активирован. Попробуй через 5 секунд.")

    elif cmd == "set_token":
        token = args[0]
        req = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
        if req.get("ok"):
            bot_user = req["result"]["username"]
            cfg.update({"bot_token": token, "bot_username": bot_user})
            with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)
            
            await event.edit(f"⏳ Привязываю @{bot_user} и включаю Inline Mode...")
            await setup_bot_inline(bot_user)
            
            await event.edit(f"✅ Всё готово! Бот @{bot_user} настроен. Перезагрузка...")
            await asyncio.sleep(2)
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            await event.edit("❌ Токен не валиден!")

# --- ИНЛАЙН БОТ ---
async def start_bot():
    if not cfg.get("bot_token"): return
    bot = TelegramClient('zxban_bot_session', API_ID, API_HASH)
    await bot.start(bot_token=cfg["bot_token"])
    
    @bot.on(events.InlineQuery)
    async def i_handler(event):
        if event.text == 'config_menu':
            await event.answer([event.builder.article('Zxban', text='⚙️ Меню управления', buttons=[
                [Button.inline("📦 Модули", data="m_list")],
                [Button.inline("🔄 Рестарт", data="reboot")]
            ])])

    @bot.on(events.CallbackQuery)
    async def cb(event):
        if event.data == b"m_list":
            mods = "\n".join([f"• {m}" for m in loaded_modules.keys()]) or "Пусто"
            await event.edit(f"🧩 **Загруженные модули:**\n{mods}", buttons=[Button.inline("⬅️ Назад", data="back")])
        elif event.data == b"reboot":
            os.execl(sys.executable, sys.executable, *sys.argv)

async def main():
    load_modules()
    await client.start()
    await start_bot()
    print("🚀 Zxban запущен и готов к работе!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
