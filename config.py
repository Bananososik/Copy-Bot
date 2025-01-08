import os
import json
import uuid
from login import *

class Config:
    API_ID = API_ID
    API_HASH = API_HASH
    BOT_TOKEN = BOT_TOKEN
    SESSION_NAME = SESSION_NAME
    WORKERS = WORKERS
    WORK_DIR = WORK_DIR
    AUTHORIZED_USER_ID = AUTHORIZED_USER_ID
    PHONE_NUMBER = PHONE_NUMBER
    
    TASKS_FILE = os.path.join(WORK_DIR, "tasks.json")
    TASKS = []

    @staticmethod
    def load_tasks():
        if os.path.exists(Config.TASKS_FILE):
            with open(Config.TASKS_FILE, "r", encoding="utf-8") as file:
                Config.TASKS = json.load(file)
        else:
            Config.TASKS = []

    @staticmethod
    def load_tasks():
        if os.path.exists(Config.TASKS_FILE):
            try:
                with open(Config.TASKS_FILE, "r", encoding="utf-8") as file:
                    loaded_tasks = json.load(file)
                    # Проверяем и конвертируем старый формат если нужно
                    for task in loaded_tasks:
                        if "from" in task and "from_id" not in task:
                            task["from_id"] = task.pop("from")
                        if "to" in task and "to_id" not in task:
                            task["to_id"] = task.pop("to")
                    Config.TASKS = loaded_tasks
            except Exception as e:
                print(f"Ошибка при загрузке задач: {str(e)}")
                Config.TASKS = []
        else:
            Config.TASKS = []

    @staticmethod
    def save_tasks():
        try:
            with open(Config.TASKS_FILE, "w", encoding="utf-8") as file:
                json.dump(Config.TASKS, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении задач: {str(e)}")

# Загружаем задачи при запуске
Config.load_tasks()