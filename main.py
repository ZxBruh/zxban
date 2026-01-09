import time, json, os, sys, subprocess, importlib, random, string
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from telethon import TelegramClient, events, Button, functions, types
from telethon.tl.types import MessageEntityCustomEmoji

# --- КОНФИГУРАЦИЯ ---
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'
MODULES_DIR = 'modules'

def load_config():
    default = {
        "prefix": "!",
        "bot_token": "",
        "bot_username": "",
        "info_template": "🛡️ **Zxban Status: Online**",
        "ping_template": "⚡ **Pong!** `{time}` ms"
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
        return default
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        current = json.load(f)
    for k, v in default.items():
        if k not in current: current[k] = v
    return current

cfg = load_config()
client = TelegramClient('zxban_session', API_ID, API_HASH)
bot_client = None

loaded_modules = {}

def load_module(file_path):
    module_name = os.path.basename(file_path)[:-3]
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        loaded_modules[module_name] = mod
        print(f"✅ Модуль {module_name} загружен")
        return True
    except Exception as e:
        print(f"❌ Ошибка в модуле {module_name}: {e}")
        return False

@client.on(events.NewMessage(outgoing=True))
async def main_handler(event):
    global cfg
    prefix = cfg.get("prefix", "!")
    if not event.raw_text.startswith(prefix): return
    args = event.raw_text[len(prefix):].split()
    if not args: return
    cmd = args[0].lower()

    if cmd == "кфг":
        if not cfg.get("bot_token") or not cfg.get("bot_username"):
            await event.edit("⚠️ Токен или Username бота не настроены! Введи `!set_token <токен>`.")
            return
        await event.delete()
        try:
            results = await client.inline_query(cfg['bot_username'], 'config_menu')
            if results:
                await results[0].click(event.chat_id)
        except Exception as e:
            print(f"Inline error: {e}")

    elif cmd == "set_token":
        if len(args) > 1:
            token = args[1]
            await event.edit("⏳ Проверка токена...")
            try:
                # Временный запуск бота для получения инфы
                temp_bot = TelegramClient('temp_session', API_ID, API_HASH)
                await temp_bot.start(bot_token=token)
                bot_me = await temp_bot.get_me()
                await temp_bot.disconnect()

                cfg['bot_token'] = token
                cfg['bot_username'] = bot_me.username
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=4)
                
                await event.edit(f"✅ Токен привязан к **@{bot_me.username}**! Перезагрузка...")
                os.execl(sys.executable, sys.executable, *sys.argv)
            except Exception as e:
                await event.edit(f"❌ Ошибка: {e}")
        else:
            await event.edit("📝 Используй: `!set_token <твой_токен>`")

# --- ЛОГИКА БОТА (ИНЛАЙН И КНОПКИ) ---
async def start_bot():
    global bot_client
    if cfg.get("bot_token"):
        try:
            bot_client = TelegramClient('zxban_bot', API_ID, API_HASH)
            await bot_client.start(bot_token=cfg["bot_token"])
            
            @bot_client.on(events.InlineQuery)
            async def inline_handler(event):
                if event.text == 'config_menu':
                    await event.answer([
                        event.builder.article('Settings', text='⚙️ **Настройки Zxban**', buttons=[
                            [Button.inline("📦 Встроенные", data="mods_int")],
                            [Button.inline("🌐 Внешние", data="mods_ext")]
                        ])
                    ])

            @bot_client.on(events.CallbackQuery)
            async def cb_handler(event):
                if event.data == b"mods_int":
                    await event.edit("🛠 **Встроенные модули:**\n• Core\n• Loader\n• Update", 
                                     buttons=[[Button.inline("🌐 Внешние", data="mods_ext")]])
                elif event.data == b"mods_ext":
                    buttons = []
                    mod_names = list(loaded_modules.keys())
                    if not mod_names:
                        await event.answer("Нет загруженных модулей", alert=True)
                        return
                    for i in range(0, len(mod_names), 2):
                        row = [Button.inline(f"🧩 {name}", data=f"modinfo_{name}") for name in mod_names[i:i+2]]
                        buttons.append(row)
                    buttons.append([Button.inline("📦 Встроенные", data="mods_int")])
                    await event.edit("📂 **Список внешних модулей:**", buttons=buttons)
                elif event.data.startswith(b"modinfo_"):
                    mod_name = event.data.decode().split("_")[1]
                    await event.answer(f"Модуль {mod_name} активен", alert=True)
        except Exception as e:
            print(f"Ошибка запуска бота: {e}")

async def main():
    if not os.path.exists(MODULES_DIR):
        os.makedirs(MODULES_DIR)
    
    for file in os.listdir(MODULES_DIR):
        if file.endswith(".py"): 
            load_module(os.path.join(MODULES_DIR, file))
            
    await client.start()
    await start_bot()
    print(f"Zxban запущен!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
