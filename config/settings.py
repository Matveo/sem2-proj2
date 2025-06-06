import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ru": "Русский",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch"
}

# Настройки логирования
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"

# Список ID администраторов
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = []
if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip()]
    except ValueError:
        print("Ошибка: неверный формат ADMIN_IDS в .env файле")
        ADMIN_IDS = []

# Настройки API
TRANSLATION_API_URL = os.getenv("TRANSLATION_API_URL", "https://ftapi.pythonanywhere.com/")

# Максимальная длина текста для перевода
MAX_TEXT_LENGTH = 4000

# Путь к файлу истории
HISTORY_FILE = "storage/history.json"