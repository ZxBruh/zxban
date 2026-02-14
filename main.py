import os, sys, importlib, json
from telethon import TelegramClient, events

# ТВОИ ДАННЫЕ (API_ID и API_HASH менять не обязательно, это стандартные)
API_ID = 2040 
API_HASH = 'b18441a1ff607e10a989891a5462e627'
MODULES_DIR = 'modules'

client = TelegramClient('zxban_session', API_ID, API_HASH)

def load_modules():
    """Функция для регистрации команд из папки modules"""
    if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)
    count = 0
    for file in os.listdir(MODULES_DIR):
        if file.endswith(".py"):
            name = file[:-3]
            try:
                spec = importlib.util.spec_from_file_location(name, f"{MODULES_DIR}/{file}")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for attr in dir(mod):
                    handler = getattr(mod, attr)
                    if hasattr(handler, 'callback'):
                        client.add_event_handler(handler)
                count += 1
                print(f"✅ Модуль {name} загружен")
            except Exception as e:
                print(f"❌ Ошибка в модуле {name}: {e}")
    return count

@client.on(events.NewMessage(outgoing=True, pattern=r'\!пинг'))
async def ping(event):
    await event.edit("🚀 **Zxban онлайн!**")

async def main():
    print("🛰 Запуск Zxban...")
    count = load_modules()
    await client.start()
    print(f"🚀 Работает! Загружено модулей: {count}")
    print("Напиши !пинг в любом чате для проверки.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
