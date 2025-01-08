from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from bot import JunctionBot
import asyncio


# Проверка авторизованного пользователя
def is_authorized_user(_, __, m: Message):
    return m.from_user.id == Config.AUTHORIZED_USER_ID

# Инициализация пользовательского клиента
user_client = Client(
    "user_session",  # Имя вашей сессии
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    no_updates=True
)

async def get_chats(message: Message):
    try:
        # Проверяем, не запущен ли уже клиент
        if not user_client.is_connected:
            await user_client.start()
            
        # Получаем диалоги
        dialogs = []
        async for dialog in user_client.get_dialogs(limit=10):
            dialogs.append(dialog)
            
        # Остальной код остается тем же
        chat_list = []
        for dialog in dialogs:
            chat_info = {
                "title": str(dialog.chat.title) or 'None',
                "id": str(dialog.chat.id),
                "type": str(dialog.chat.type)
            }
            if "GROUP" in chat_info['type'] or "SUPERGROUP" in chat_info["type"]:
                chat_list.append(chat_info)
                
        chat_list_str = "\n".join(
            f"{index + 1}. Название чата: {chat['title']}\n    ID: {chat['id']}\n"
            for index, chat in enumerate(chat_list)
        )
        
        if chat_list_str:
            await message.reply_text(f"Последние групповые чаты:\n{chat_list_str}")
        else:
            await message.reply_text("Групповые чаты не найдены.")
            
        return chat_list
        
    except Exception as e:
        await message.reply_text(f"Произошла ошибка при получении чатов: {e}")
        return []
    finally:
        if user_client.is_connected:
            await user_client.stop()
            

# Словарь для хранения состояний пользователей
user_states = {}
chat_lists = {}

@JunctionBot.on_message(filters.command("Добавить_задачу") & filters.create(is_authorized_user))
async def add_task(client, message: Message):
    try:
        # Инициализируем состояние пользователя
        user_id = message.from_user.id
        user_states[user_id] = {"stage": "select_from", "from": None, "to": None}

        # Получаем список чатов и сохраняем его
        chatlist = await get_chats(message)
        if not chatlist:
            return
        
        # Сохраняем список чатов для этого пользователя
        chat_lists[user_id] = chatlist

        # Формируем клавиатуру
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"{i + 1}. {chat['title']}", 
                callback_data=f"chat_{i}"
            )] for i, chat in enumerate(chatlist)
        ])

        await message.reply_text(
            "Выберите группу, откуда пересылать сообщения:",
            reply_markup=keyboard
        )

    except Exception as e:
        await message.reply_text(f"Произошла ошибка: {e}")

# Обработчик callback query на уровне модуля
@JunctionBot.on_callback_query(filters.regex(r"chat_(\d+)"))
async def handle_chat_selection(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        
        # Проверяем, существует ли состояние пользователя
        if user_id not in user_states or user_id not in chat_lists:
            await callback_query.answer("Сессия истекла. Пожалуйста, начните заново.")
            return

        selected_chat_index = int(callback_query.data.split("_")[1])
        selected_chat = chat_lists[user_id][selected_chat_index]
        user_state = user_states[user_id]

        if user_state["stage"] == "select_from":
            # Сохраняем выбранный чат отправителя
            user_state["from"] = selected_chat["id"]
            user_state["stage"] = "select_to"
            
            # Формируем новую клавиатуру для выбора получателя
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    f"{i + 1}. {chat['title']}", 
                    callback_data=f"chat_{i}"
                )] for i, chat in enumerate(chat_lists[user_id])
            ])

            await callback_query.message.edit_text(
                "Теперь выберите группу, куда пересылать сообщения:",
                reply_markup=keyboard
            )
            await callback_query.answer(f"Выбрана группа отправителя: {selected_chat['title']}")

        elif user_state["stage"] == "select_to":
            # Сохраняем выбранный чат получателя и его название
            user_state["to"] = selected_chat["id"]
            
            # Получаем названия чатов
            from_chat_title = next(chat["title"] for chat in chat_lists[user_id] 
                                if chat["id"] == user_state["from"])
            to_chat_title = selected_chat["title"]
            
            # Создаем новую задачу
            task = {
                "id": len(Config.TASKS) + 1,  # Простая нумерация
                "from_id": user_state["from"],
                "to_id": user_state["to"],
                "from_title": from_chat_title,
                "to_title": to_chat_title
            }
            Config.TASKS.append(task)
            Config.save_tasks()

            # Отправляем подтверждение
            await callback_query.message.edit_text(
                f"Задача #{task['id']} добавлена:\n"
                f"Откуда: {task['from_title']}\n"
                f"Куда: {task['to_title']}"
            )
            await callback_query.answer("Задача успешно создана!")

            # Очищаем состояние пользователя
            del user_states[user_id]
            del chat_lists[user_id]

    except Exception as e:
        await callback_query.answer(f"Произошла ошибка: {str(e)}")

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