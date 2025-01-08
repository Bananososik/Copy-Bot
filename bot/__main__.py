import os
from config import Config
from bot import JunctionBot
from pyrogram import filters
from pyrogram.types import Message
from bot.utils.forward_message import forward_message
import bot.plugins.settings


# Создаем рабочую директорию, если она не существует
if not os.path.exists(Config.WORK_DIR):
    os.makedirs(Config.WORK_DIR)

# Инициализация бота
config = Config()
bot = JunctionBot(config)

def forward_filter(_, __, m: Message):
    for task in Config.TASKS:
        if m.chat.id == int(task["from_id"]):  # Изменено с "from" на "from_id"
            return True
    return False

# Также нужно изменить функцию forward_message в bot/utils/forward_message.py:

async def forward_message(client, message):
    try:
        for task in Config.TASKS:
            if message.chat.id == int(task["from_id"]):  # Изменено с "from" на "from_id"
                await message.forward(
                    chat_id=int(task["to_id"])  # Изменено с "to" на "to_id"
                )
    except Exception as e:
        print(f"Ошибка при пересылке сообщения: {str(e)}")

# Запуск бота
if __name__ == "__main__":
    bot.run()