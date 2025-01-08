from pyrogram import filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from bot import JunctionBot

@JunctionBot.on_message(filters.command("start") & filters.incoming & filters.private)
async def start(c: JunctionBot, m: Message):
    # Создаем клавиатуру с командами
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("/Добавить_задачу")],
            [KeyboardButton("/Удалить_задачу")],
            [KeyboardButton("/Задачи")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await m.reply_text(
        "Привет, это бот для пересылки сообщений. Я могу пересылать сообщения из одного чата в другой.\n\nКоманды которые вы можете использовать появились у вас в клавиатуре",
        reply_markup=keyboard,
        reply_to_message_id=m.id
    )
