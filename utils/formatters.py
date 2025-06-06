import json
import os
from typing import Dict, Any

# Глобальный кэш для хранения пользовательских настроек
# В реальном проекте лучше использовать базу данных
USER_SETTINGS = {}

def get_message(lang_code: str, key: str) -> str:
    """
    Получает локализованное сообщение по коду языка и ключу
    """
    # Определяем путь к файлу локализации
    locale_file = f"locales/{lang_code}.json"
      # Если файл не найден, используем английский по умолчанию
    if not os.path.exists(locale_file):
        locale_file = "locales/en.json"
    
    try:
        with open(locale_file, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        result = messages.get(key, f"Message '{key}' not found")
        return result
    except FileNotFoundError:
        return f"Locale file not found for '{lang_code}'"
    except json.JSONDecodeError:
        return f"Invalid JSON in locale file for '{lang_code}'"

def get_user_language(user_id: int) -> str:
    """
    Получает язык пользователя из пользовательских настроек
    """
    # Если пользователь есть в кэше настроек, возвращаем его язык
    if user_id in USER_SETTINGS and "language" in USER_SETTINGS[user_id]:
        return USER_SETTINGS[user_id]["language"]
    
    # Иначе возвращаем английский по умолчанию
    return "en"

def set_user_language(user_id: int, lang_code: str) -> bool:
    """
    Устанавливает язык для пользователя
    """
    try:
        # Убеждаемся, что у пользователя есть запись в настройках
        if user_id not in USER_SETTINGS:
            USER_SETTINGS[user_id] = {}
        
        # Устанавливаем язык (перезаписываем если уже существует)
        USER_SETTINGS[user_id]["language"] = lang_code
        
        # Сохраняем изменения
        save_user_settings()
        print(f"Язык пользователя {user_id} установлен: {lang_code}")
        return True
    except Exception as e:
        print(f"Ошибка при установке языка для пользователя {user_id}: {e}")
        return False

def get_user_translate_languages(user_id: int) -> Dict[str, str]:
    """
    Получает языки перевода пользователя
    """
    if user_id in USER_SETTINGS and "translate" in USER_SETTINGS[user_id]:
        return USER_SETTINGS[user_id]["translate"]
    
    # Возвращаем языки по умолчанию
    return {
        "source": "auto",  # auto для автоопределения
        "target": "en"     # английский по умолчанию
    }

def set_user_translate_languages(user_id: int, source: str, target: str) -> None:
    """
    Устанавливает языки перевода для пользователя
    """
    # Убеждаемся, что у пользователя есть запись в настройках
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {}
    
    # Устанавливаем языки перевода (перезаписываем если уже существует)
    USER_SETTINGS[user_id]["translate"] = {
        "source": source,
        "target": target
    }
    
    # Сохраняем изменения
    save_user_settings()
    print(f"Языки перевода пользователя {user_id} установлены: {source} -> {target}")

def swap_user_translate_languages(user_id: int) -> Dict[str, str]:
    """
    Меняет местами языки перевода пользователя
    """
    languages = get_user_translate_languages(user_id)
    
    # Если исходный язык автоопределение, то нельзя менять местами
    if languages["source"] == "auto":
        return languages
    
    # Меняем местами
    source, target = languages["target"], languages["source"]
    
    set_user_translate_languages(user_id, source, target)
    return {"source": source, "target": target}

def save_user_settings() -> None:
    """
    Сохраняет настройки пользователей в файл
    """
    try:
        # Создаем директорию если не существует
        os.makedirs("storage", exist_ok=True)
        
        # Сохраняем настройки с правильным форматированием
        with open("storage/user_settings.json", "w", encoding="utf-8") as f:
            json.dump(USER_SETTINGS, f, ensure_ascii=False, indent=2)
            
        print(f"Настройки пользователей сохранены: {len(USER_SETTINGS)} пользователей")
    except Exception as e:
        print(f"Error saving user settings: {e}")

def load_user_settings() -> None:
    """
    Загружает настройки пользователей из файла
    """
    global USER_SETTINGS
    
    try:
        if os.path.exists("storage/user_settings.json"):
            with open("storage/user_settings.json", "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:  # Проверяем, что файл не пустой
                    loaded_settings = json.loads(content)
                    # Убеждаемся, что ключи - это строки (ID пользователей)
                    USER_SETTINGS = {int(k) if k.isdigit() else k: v for k, v in loaded_settings.items()}
                else:
                    USER_SETTINGS = {}
        else:
            USER_SETTINGS = {}
            print("Файл настроек пользователей не найден, создается новый")
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON в настройках пользователей: {e}")
        USER_SETTINGS = {}
    except Exception as e:
        print(f"Error loading user settings: {e}")
        USER_SETTINGS = {}

# Загружаем настройки при импорте модуля
load_user_settings()

def format_translation_history(history_items: list, user_lang: str) -> str:
    """
    Форматирует историю переводов для отображения
    """
    if not history_items:
        return get_message(user_lang, "no_history")
    
    result = [get_message(user_lang, "history_message")]
    
    for i, item in enumerate(history_items, 1):
        original = item.get("original", "")
        translated = item.get("translated", "")
        from_lang = item.get("from_lang", "").upper()
        to_lang = item.get("to_lang", "").upper()
        
        entry = (
            f"{i}. <b>{original}</b>\n"
            f"🔄 {from_lang} ➡️ {to_lang}\n"
            f"{translated}\n"
        )
        
        result.append(entry)
    
    return "\n".join(result)

def get_user_settings(user_id: int) -> Dict[str, Any]:
    """
    Получает все настройки пользователя
    """
    return USER_SETTINGS.get(user_id, {})

def clear_user_settings(user_id: int) -> bool:
    """
    Очищает все настройки пользователя
    """
    if user_id in USER_SETTINGS:
        del USER_SETTINGS[user_id]
        save_user_settings()
        print(f"Настройки пользователя {user_id} очищены")
        return True
    return False

def get_all_users_count() -> int:
    """
    Возвращает количество пользователей с сохраненными настройками
    """
    return len(USER_SETTINGS)

def backup_user_settings(backup_file: str = "storage/user_settings_backup.json") -> bool:
    """
    Создает резервную копию настроек пользователей
    """
    try:
        os.makedirs("storage", exist_ok=True)
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(USER_SETTINGS, f, ensure_ascii=False, indent=2)
        print(f"Резервная копия настроек создана: {backup_file}")
        return True
    except Exception as e:
        print(f"Ошибка создания резервной копии: {e}")
        return False