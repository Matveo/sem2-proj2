import json
import os
from typing import Dict, List
from datetime import datetime
from utils.logger import logger

HISTORY_FILE = "storage/history.json"

def load_history() -> Dict:
    """
    Загружает историю переводов из файла
    """
    if not os.path.exists(HISTORY_FILE):
        return {}
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Ошибка при загрузке истории: {e}")
        return {}

def save_history(history: Dict) -> bool:
    """
    Сохраняет историю переводов в файл
    """
    try:
        # Создаем директорию если её нет
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении истории: {e}")
        return False

def add_to_history(user_id: int, record: Dict) -> bool:
    """
    Добавляет запись в историю переводов пользователя
    
    Args:
        user_id: ID пользователя
        record: Словарь с данными перевода
    """
    try:
        history = load_history()
        user_id_str = str(user_id)
        
        if user_id_str not in history:
            history[user_id_str] = []
        
        # Добавляем временную метку
        record["timestamp"] = datetime.now().isoformat()
        
        # Добавляем запись в начало списка
        history[user_id_str].insert(0, record)
        
        # Ограничиваем количество записей (максимум 50)
        history[user_id_str] = history[user_id_str][:50]
        
        return save_history(history)
    except Exception as e:
        logger.error(f"Ошибка при добавлении в историю: {e}")
        return False

def get_history(user_id: int, limit: int = 5) -> List[Dict]:
    """
    Получает историю переводов пользователя
    
    Args:
        user_id: ID пользователя
        limit: Максимальное количество записей
    """
    try:
        history = load_history()
        user_id_str = str(user_id)
        
        user_history = history.get(user_id_str, [])
        return user_history[:limit]
    except Exception as e:
        logger.error(f"Ошибка при получении истории: {e}")
        return []

def clear_history(user_id: int) -> bool:
    """
    Очищает историю переводов пользователя
    """
    try:
        history = load_history()
        user_id_str = str(user_id)
        
        if user_id_str in history:
            del history[user_id_str]
            return save_history(history)
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке истории: {e}")
        return False
