import time
import json
import os
import io
import sys
import subprocess
from contextlib import redirect_stdout
from telethon import TelegramClient, events

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "info_template": "**🛡️ Юзербот Zxban**\n---\n**Статус:** Работает\n**Платформа:** Termux",
            "ping_template": "**🏓 Понг!**\nЗадержка: `{time}` мс",
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

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}инфо'))
async def info(event):
    cfg = load_config()
    await event.edit(cfg.get("info_template", "Ошибка: шаблон не найден"))

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}хелп'))
async def help_cmd(event):
    cfg = load_config()
    await event.edit(cfg.get("help_template", "Ошибка: шаблон не найден"))

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}пинг'))
async def ping(event):
    cfg = load_config()
    start = time.time()
    await event.edit("🚀 Проверяю...")
    ms = round((time.time() - start) * 1000)
    text = cfg.get("ping_template", "Понг: {time}").replace("{time}", str(ms))
    await event.edit(text)

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}кфг'))
async def config_cmd(event):
    cfg = load_config()
    args = event.text.split(maxsplit=2)
    if len(args) < 3:
        return await event.edit(f"**Формат:** `{PREFIX}кфг [пинг/инфо/хелп] [текст]`")
    key = args[1].lower()
    if key in ["пинг", "инфо", "хелп"]:
        cfg[f"{key}_template"] = args[2]
        save_config(cfg)
        await event.edit(f"✅ Настройка `{key}` обновлена!")
    else:
        await event.edit("❌ Используй: пинг, инфо, хелп")

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}е'))
async def execute_cmd(event):
    code = event.text.split(maxsplit=1)
    if len(code) < 2: return await event.edit("Введите код!")
    await event.edit("<b>Выполняю...</b>", parse_mode='html')
    f = io.StringIO()
    try:
        with redirect_stdout(f):
            exec(code[1])
        await event.edit(f"**Код:**\n`{code[1]}`\n\n**Результат:**\n`{f.getvalue()}`")
    except Exception as e:
        await event.edit(f"**Ошибка:**\n`{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}терминал'))
async def terminal_cmd(event):
    cmd = event.text.split(maxsplit=1)
    if len(cmd) < 2: return await event.edit("Введите команду!")
    await event.edit(f"<code>Запуск: {cmd[1]}</code>", parse_mode='html')
    process = subprocess.Popen(cmd[1], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    await event.edit(f"**Терминал:**\n`{stdout or stderr}`")

@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}апдейт'))
async def update_cmd(event):
    await event.edit("🔄 **Обновление...**")
    try:
        process = subprocess.Popen(["git", "pull", "https://github.com/ZxBruh/zxban"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, _ = process.communicate()
        if "Already up to date" in stdout:
            return await event.edit("✅ **Последняя версия уже установлена**")
        await event.edit("✅ **Обновлено. Рестарт...**")
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await event.edit(f"❌ **Ошибка:** `{e}`")

async def main():
    print("--- Юзербот Zxban запускается ---")
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
