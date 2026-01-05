import time
import json
import os
import io
import subprocess
from contextlib import redirect_stdout
from telethon import TelegramClient, events

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
API_ID = 2040  # Замени на свой
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'

# Функции работы с конфигом
def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "info_template": "**🛡️ Юзербот Zxban**\n**Статус:** OK",
            "ping_template": "**🏓 Понг!**\nЗадержка: `{time}` мс",
            "prefix": "!"
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# Инициализация
config = load_config()
PREFIX = config.get("prefix", "!")
client = TelegramClient('zxban_session', API_ID, API_HASH)

print(f"--- Юзербот запущен! Префикс: {PREFIX} ---")

# Команда !инфо
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}инфо'))
async def info(event):
    cfg = load_config()
    await event.edit(cfg["info_template"])

# Команда !пинг
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}пинг'))
async def ping(event):
    cfg = load_config()
    start = time.time()
    await event.edit("🚀 Проверяю...")
    end = time.time()
    ms = round((end - start) * 1000)
    # Заменяем {time} в шаблоне на реальное число
    text = cfg["ping_template"].replace("{time}", str(ms))
    await event.edit(text)

# Команда !кфг (изменение настроек)
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}кфг'))
async def config_cmd(event):
    cfg = load_config()
    args = event.text.split(maxsplit=2)
    
    if len(args) < 3:
        return await event.edit(f"**Формат:** `{PREFIX}кфг [пинг/инфо] [текст]`")

    key = args[1].lower()
    value = args[2]

    if key == "пинг":
        cfg["ping_template"] = value
    elif key == "инфо":
        cfg["info_template"] = value
    else:
        return await event.edit("❌ Ключ не найден (используй: пинг, инфо)")

    save_config(cfg)
    await event.edit(f"✅ Настройка `{key}` обновлена!")

# Команда !е (выполнение Python кода)
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}е'))
async def execute_cmd(event):
    code = event.text.split(maxsplit=1)
    if len(code) < 2:
        return await event.edit("Введите код!")
    
    code = code[1]
    await event.edit("<b>Выполняю...</b>", parse_mode='html')
    
    f = io.StringIO()
    try:
        with redirect_stdout(f):
            exec(code)
        out = f.getvalue()
        await event.edit(f"**Код:**\n`{code}`\n\n**Результат:**\n`{out}`")
    except Exception as e:
        await event.edit(f"**Ошибка:**\n`{e}`")

# Команда !терминал
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}терминал'))
async def terminal_cmd(event):
    cmd = event.text.split(maxsplit=1)
    if len(cmd) < 2:
        return await event.edit("Введите команду!")

    await event.edit(f"<code>Запуск: {cmd[1]}</code>", parse_mode='html')
    process = subprocess.Popen(cmd[1], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    
    result = stdout or stderr
    await event.edit(f"**Терминал:**\n`{result}`")

async def main():
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
