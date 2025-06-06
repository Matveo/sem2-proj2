"""
Конфигурация антиспам системы
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Базовые настройки антиспам
DEFAULT_RATE_LIMIT = int(os.getenv("ANTISPAM_RATE_LIMIT", 5))  # Максимум сообщений в временном окне
DEFAULT_WINDOW_TIME = int(os.getenv("ANTISPAM_WINDOW_TIME", 60))  # Временное окно в секундах
DEFAULT_BLOCK_TIME = int(os.getenv("ANTISPAM_BLOCK_TIME", 20))  # Время блокировки в секундах (5 минут)
DEFAULT_WARNING_THRESHOLD = 3  # Количество сообщений для предупреждения
DEFAULT_MAX_MESSAGE_LENGTH = int(os.getenv("ANTISPAM_MAX_MESSAGE_LENGTH", 3000))  # Максимальная длина сообщения

# Продвинутые настройки для разных типов пользователей
USER_CONFIGS = {
    'default': {
        'rate_limit': 5,
        'window_time': 60,
        'block_time': 10,
        'warning_threshold': 3,
        'max_message_length': 2000
    },
    'new_user': {  # Для новых пользователей (строже)
        'rate_limit': 3,
        'window_time': 60,
        'block_time': 20,
        'warning_threshold': 2,
        'max_message_length': 1000
    },
    'trusted_user': {  # Для проверенных пользователей (мягче)
        'rate_limit': 10,
        'window_time': 60,
        'block_time': 5,
        'warning_threshold': 7,
        'max_message_length': 3000
    }
}

# ID администраторов (не подвергаются антиспам проверкам)
# Получаем из переменной окружения ADMIN_IDS (строка с ID, разделенными запятыми)
def get_admin_ids() -> list:
    """
    Получает список ID администраторов из переменной окружения
    
    Returns:
        list: Список ID администраторов
    """
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str.strip():
        return []
    
    try:
        # Разбиваем строку по запятым и преобразуем в int
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(',') if id_str.strip()]
        return admin_ids
    except ValueError as e:
        print(f"Ошибка при парсинге ADMIN_IDS: {e}")
        return []

# Получаем список администраторов при импорте модуля
ADMIN_IDS = get_admin_ids()

# Команды, которые не учитываются в rate limiting
EXCLUDED_COMMANDS = [
    '/start',
    '/help',
    # Другие важные команды которые не должны блокироваться
]

# Callback data, которые не учитываются в rate limiting
EXCLUDED_CALLBACKS = [
    'main_menu',
    'help',
    'close',
    # Другие важные колбэки
]

def get_user_config(user_id: int, user_type: str = 'default') -> dict:
    """
    Получает конфигурацию антиспам для пользователя
    
    Args:
        user_id: ID пользователя
        user_type: Тип пользователя ('default', 'new_user', 'trusted_user')
    
    Returns:
        dict: Конфигурация антиспам
    """
    return USER_CONFIGS.get(user_type, USER_CONFIGS['default'])

def is_excluded_command(text: str) -> bool:
    """
    Проверяет, является ли команда исключенной из антиспам проверок
    
    Args:
        text: Текст сообщения
    
    Returns:
        bool: True если команда исключена
    """
    if not text or not text.startswith('/'):
        return False
    
    command = text.split()[0].lower()
    return command in EXCLUDED_COMMANDS

def is_excluded_callback(callback_data: str) -> bool:
    """
    Проверяет, является ли callback исключенным из антиспам проверок
    
    Args:
        callback_data: Данные callback'а
    
    Returns:
        bool: True если callback исключен
    """
    return callback_data in EXCLUDED_CALLBACKS
