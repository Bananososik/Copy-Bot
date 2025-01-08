from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from bot import JunctionBot
import asyncio


# Проверка авторизованного пользователя
def is_authorized_user(_, __, m: Message):
    return m.from_user.id == Config.AUTHORIZED_USER_ID


# Словарь для хранения состояний пользователей
user_states = {}

# Заменить старую версию add_task на новую:
@JunctionBot.on_message(filters.command("Добавить_задачу") & filters.create(is_authorized_user))
async def add_task(client, message: Message):
    try:
        # Инициализируем состояние пользователя
        user_id = message.from_user.id
        user_states[user_id] = {"stage": "waiting_from", "from": None, "to": None}

        await message.reply_text(
            "Отправьте ссылку на чат, ОТКУДА нужно пересылать сообщения\n"
            "Формат: https://t.me/channel_name или t.me/channel_name"
        )

    except Exception as e:
        await message.reply_text(f"Произошла ошибка: {e}")

# Добавить новый обработчик:
def not_command(_, __, message):
    return not message.text.startswith('/')

@JunctionBot.on_message(filters.create(is_authorized_user) & filters.create(not_command) & filters.text)
async def handle_chat_input(client, message: Message):
    try:
        user_id = message.from_user.id
        
        if user_id not in user_states:
            return

        user_state = user_states[user_id]
        chat_link = message.text.strip()

        # Извлекаем chat_identifier
        try:
            # Сначала проверяем, является ли ввод числовым ID
            if chat_link.startswith('-100'):
                chat_identifier = int(chat_link)
            else:
                # Очищаем ссылку от префиксов
                if chat_link.startswith('https://t.me/+'):
                    # Для приватных ссылок
                    await message.reply_text(
                        "Для приватных чатов используйте ID чата (начинается с -100).\n"
                        "1. Добавьте бота в чат как администратора\n"
                        "2. Перешлите любое сообщение из чата боту @RawDataBot\n"
                        "3. Скопируйте ID чата (начинается с -100) и отправьте его сюда"
                    )
                    return
                elif chat_link.startswith('https://t.me/'):
                    chat_identifier = chat_link.replace('https://t.me/', '')
                elif chat_link.startswith('t.me/'):
                    chat_identifier = chat_link.replace('t.me/', '')
                elif chat_link.startswith('@'):
                    chat_identifier = chat_link[1:]
                else:
                    chat_identifier = chat_link

            # Пробуем получить информацию о чате
            chat = await client.get_chat(chat_identifier)
            
            # Проверяем тип чата
            if chat.type not in ['group', 'supergroup', 'channel']:
                await message.reply_text(
                    "❌ Этот чат не является группой или каналом.\n"
                    "Пожалуйста, используйте только группы, супергруппы или каналы."
                )
                return

            # Проверяем права бота
            bot_member = await chat.get_member('me')
            if not bot_member.can_send_messages:
                await message.reply_text(
                    "❌ У бота нет прав для отправки сообщений в этот чат.\n"
                    "Пожалуйста, добавьте бота как администратора с правами на отправку сообщений."
                )
                return

            if user_state["stage"] == "waiting_from":
                user_state["from"] = {
                    "id": str(chat.id),
                    "title": chat.title
                }
                user_state["stage"] = "waiting_to"
                
                await message.reply_text(
                    "✅ Чат источника установлен.\n\n"
                    "Теперь отправьте чат назначения одним из способов:\n"
                    "1. ID чата (начинается с -100)\n"
                    "2. Юзернейм канала или группы (например: @channel_name)\n"
                    "3. Ссылку на канал или группу"
                )
                
            elif user_state["stage"] == "waiting_to":
                if str(chat.id) == user_state["from"]["id"]:
                    await message.reply_text("❌ Нельзя выбрать один и тот же чат для отправки и получения!")
                    return

                task = {
                    "id": len(Config.TASKS) + 1,
                    "from_id": user_state["from"]["id"],
                    "to_id": str(chat.id),
                    "from_title": user_state["from"]["title"],
                    "to_title": chat.title
                }
                
                Config.TASKS.append(task)
                Config.save_tasks()

                await message.reply_text(
                    f"✅ Задача #{task['id']} успешно добавлена!\n\n"
                    f"📤 Откуда: {task['from_title']}\n"
                    f"📥 Куда: {task['to_title']}\n"
                    f"🆔 ID источника: {task['from_id']}\n"
                    f"🆔 ID получателя: {task['to_id']}"
                )

                del user_states[user_id]

        except ValueError as ve:
            await message.reply_text(
                "❌ Неверный формат ID чата.\n"
                "ID чата должен быть числом, начинающимся с -100"
            )
        except Exception as e:
            error_message = str(e)
            if "USERNAME_NOT_OCCUPIED" in error_message:
                await message.reply_text(
                    "❌ Чат не найден!\n\n"
                    "Для публичного чата убедитесь, что:\n"
                    "1. Указан правильный юзернейм\n"
                    "2. Чат существует и доступен\n\n"
                    "Для приватного чата:\n"
                    "1. Используйте ID чата (начинается с -100)\n"
                    "2. Добавьте бота в чат как администратора\n"
                    "3. Чтобы получить ID чата, перешлите из него сообщение боту @RawDataBot"
                )
            else:
                await message.reply_text(
                    f"❌ Ошибка при получении информации о чате:\n{error_message}\n\n"
                    f"Убедитесь, что:\n"
                    f"1. Бот добавлен в чат как администратор\n"
                    f"2. У бота есть права на просмотр сообщений и отправку сообщений\n"
                    f"3. Для приватного чата используется корректный ID (начинается с -100)"
                )

    except Exception as e:
        print(f"Debug - General error: {str(e)}")
        await message.reply_text(f"❌ Произошла непредвиденная ошибка: {str(e)}")




# Обновленная функция просмотра задач
@JunctionBot.on_message(filters.command("Задачи") & filters.create(is_authorized_user))
async def list_tasks(client, message: Message):
    if not Config.TASKS:
        await message.reply_text("Нет активных задач.")
    else:
        tasks_list = "\n".join([
            f"Задача #{task['id']}\n"
            f"Откуда: {task['from_title']}\n"
            f"Куда: {task['to_title']}\n"
            for task in Config.TASKS
        ])
        await message.reply_text(f"Активные задачи:\n\n{tasks_list}")

# Обновленная функция удаления задач
@JunctionBot.on_message(filters.command("Удалить_задачу") & filters.create(is_authorized_user))
async def delete_task(client, message: Message):
    try:
        if not Config.TASKS:
            await message.reply_text("Нет активных задач для удаления.")
            return

        # Создаем клавиатуру с кнопками для каждой задачи
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"Задача #{task['id']}: {task['from_title']} → {task['to_title']}", 
                callback_data=f"del_{task['id']}"
            )] for task in Config.TASKS
        ])

        await message.reply_text(
            "Выберите задачу для удаления:",
            reply_markup=keyboard
        )

    except Exception as e:
        await message.reply_text(f"Произошла ошибка: {e}")

# Обработчик для подтверждения удаления
@JunctionBot.on_callback_query(filters.regex(r"del_(\d+)"))
async def handle_delete_confirmation(client, callback_query):
    try:
        # Извлекаем ID задачи из callback_data
        task_id = int(callback_query.data.split("_")[1])
        task = next((task for task in Config.TASKS if task["id"] == task_id), None)
        
        if not task:
            await callback_query.answer("Задача не найдена.")
            return

        # Создаем клавиатуру для подтверждения
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_{task_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_{task_id}")
            ]
        ])

        await callback_query.message.edit_text(
            f"Вы уверены, что хотите удалить задачу #{task_id}?\n"
            f"Откуда: {task['from_title']}\n"
            f"Куда: {task['to_title']}",
            reply_markup=keyboard
        )

    except Exception as e:
        await callback_query.answer(f"Произошла ошибка: {str(e)}")

# Обработчик для финального подтверждения/отмены удаления
@JunctionBot.on_callback_query(filters.regex(r"(confirm|cancel)_(\d+)"))
async def handle_delete_final(client, callback_query):
    try:
        action, task_id = callback_query.data.split("_")
        task_id = int(task_id)
        
        if action == "cancel":
            await callback_query.message.edit_text("❌ Удаление отменено.")
            return

        task_index = next((index for index, task in enumerate(Config.TASKS) 
                          if task["id"] == task_id), None)
        
        if task_index is not None:
            # Сохраняем информацию о задаче перед удалением
            deleted_task = Config.TASKS[task_index]
            del Config.TASKS[task_index]
            Config.save_tasks()
            
            # Обновляем ID оставшихся задач
            for i, task in enumerate(Config.TASKS, 1):
                task["id"] = i
            Config.save_tasks()
            
            await callback_query.message.edit_text(
                f"✅ Задача #{task_id} успешно удалена:\n"
                f"Откуда: {deleted_task['from_title']}\n"
                f"Куда: {deleted_task['to_title']}"
            )
        else:
            await callback_query.message.edit_text("❌ Задача не найдена.")

    except Exception as e:
        print(f"Ошибка при удалении задачи: {str(e)}")  # Добавляем логирование
        await callback_query.answer("Произошла ошибка при удалении задачи")