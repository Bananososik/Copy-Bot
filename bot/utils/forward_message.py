from pyrogram.types import Message
from bot import JunctionBot
from config import Config

async def forward_message(c: JunctionBot, m: Message):
    for task in Config.TASKS:
        # Проверяем, что сообщение пришло из группы "откуда"
        if m.chat.id == int(task["from_id"]):
            try:
                if m.video:
                    await c.send_video(int(task["to_id"]), m.video.file_id, caption=m.caption)
            except Exception as e:
                print(f"Ошибка при отправке сообщения в чат {task['to_id']}: {e}")