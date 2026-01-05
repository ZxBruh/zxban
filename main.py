import time, json, os, io, sys, subprocess, importlib

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from contextlib import redirect_stdout
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'
MODULES_DIR = 'modules'

if not os.path.exists(MODULES_DIR):
    os.makedirs(MODULES_DIR)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {"info_template": "🛡️ **Zxban Status**", "ping_template": "⚡ **Pong!** `{time}` ms", "prefix": "!"}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()
client = TelegramClient('zxban_session', API_ID, API_HASH)
loaded_modules = {}

def load_module(file_path):
    module_name = os.path.basename(file_path)[:-3]
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        loaded_modules[module_name] = mod
        if hasattr(mod, "init"): mod.init(client)
        return True
    except Exception: return False

def load_all_modules():
    for file in os.listdir(MODULES_DIR):
        if file.endswith(".py"): load_module(os.path.join(MODULES_DIR, file))

async def edit_with_emoji(event, text, emoji_id):
    await event.edit(text, formatting_entities=[MessageEntityCustomEmoji(offset=0, length=2, document_id=emoji_id)])

@client.on(events.NewMessage(outgoing=True))
async def main_handler(event):
    global cfg
    prefix = cfg.get("prefix", "!")
    text = event.raw_text
    if not text.startswith(prefix): return
    args = text[len(prefix):].split()
    if not args: return
    cmd = args[0].lower()

    if cmd == "инфо":
        await edit_with_emoji(event, f"🛡️ {cfg['info_template']}", 5431682333653110201)

    elif cmd == "пинг":
        start = time.time()
        await event.edit("🚀")
        ms = round((time.time() - start) * 1000)
        # ИСПРАВЛЕННАЯ СТРОКА ТУТ:
        await edit_with_emoji(event, f"⚡ {cfg['ping_template'].replace('{time}', str(ms))}", 5447103212130101411)

    elif cmd == "загрузить":
        reply = await event.get_reply_message()
        if reply and reply.file and reply.file.name.endswith(".py"):
            path = await reply.download_media(file=MODULES_DIR)
            if load_module(path): await event.edit(f"✅ Модуль `{os.path.basename(path)}` загружен")
            else: await event.edit("❌ Ошибка модуля")
        elif len(args) > 1 and args[1].startswith("http"):
            url = args[1].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            name = url.split("/")[-1]
            r = requests.get(url)
            path = os.path.join(MODULES_DIR, name)
            with open(path, "wb") as f: f.write(r.content)
            if load_module(path): await event.edit(f"✅ `{name}` загружен")
            else: await event.edit("❌ Ошибка")

    elif cmd == "префикс":
        if len(args) > 1:
            cfg['prefix'] = args[1]
            with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)
            await event.edit(f"✅ Префикс: `{args[1]}`. Рестарт...")
            os.execl(sys.executable, sys.executable, *sys.argv)

    elif cmd == "кфг":
        btns = [[Button.inline("📦 Встроенные", data="mods_int")], [Button.inline("🌐 Внешние", data="mods_ext")]]
        await event.edit("**⚙️ Настройки Zxban**", buttons=btns)

    elif cmd == "апдейт":
        msg = await event.edit("🔄 **Запуск обновления...**")
        try:
            subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE).communicate()
            await msg.edit("✅ **Данные синхронизированы! Перезагрузка...**")
            time.sleep(1)
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            await event.edit(f"❌ Ошибка: {e}")

@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    if data == "mods_int":
        await event.edit("🛠 **Встроенные:**\n• Loader\n• Config\n• Update", buttons=[Button.inline("⬅️ Назад", data="back")])
    elif data == "mods_ext":
        mods = "\n".join([f"• {m}.py" for m in loaded_modules.keys()]) or "Нет модулей"
        await event.edit(f"📂 **Внешние:**\n{mods}", buttons=[Button.inline("⬅️ Назад", data="back")])
    elif data == "back":
        btns = [[Button.inline("📦 Встроенные", data="mods_int")], [Button.inline("🌐 Внешние", data="mods_ext")]]
        await event.edit("**⚙️ Настройки Zxban**", buttons=btns)

async def main():
    load_all_modules()
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
