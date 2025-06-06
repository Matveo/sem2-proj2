from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List
import json

def help_inline_keyboard(lang_code="en"):
    """
    Создает inline-клавиатуру для команды help
    """
    # Текст кнопок в зависимости от языка
    button_text = {
        "en": ["🔄 Translate", "🌐 Language", "📋 History", "ℹ️ About", "🏠 Main Menu"],
        "ru": ["🔄 Перевести", "🌐 Язык", "📋 История", "ℹ️ О боте", "🏠 Главное меню"]
    }
    
    texts = button_text.get(lang_code, button_text["en"])
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts[0], callback_data="translate"),
                InlineKeyboardButton(text=texts[1], callback_data="setlanguage")
            ],
            [
                InlineKeyboardButton(text=texts[2], callback_data="history"),
                InlineKeyboardButton(text=texts[3], callback_data="about")
            ],
            [
                InlineKeyboardButton(text=texts[4], callback_data="main_menu")
            ]
        ]
    )

def about_inline_keyboard(lang_code="en"):
    """
    Создает inline-клавиатуру для информации о боте
    """
    back_text = "🔙 Back to Help" if lang_code == "en" else "🔙 Назад к помощи"
    menu_text = "🏠 Main Menu" if lang_code == "en" else "🏠 Главное меню"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=back_text, callback_data="help"),
                InlineKeyboardButton(text=menu_text, callback_data="main_menu")
            ]
        ]
    )

def main_menu_inline_keyboard(lang_code="en"):
    """
    Создает основную inline-клавиатуру с командами вместо reply клавиатуры
    """
    # Текст кнопок в зависимости от языка
    button_text = {
        "en": ["🔄 Translate", "❔ Help", "🌐 Change Language", "📋 History", "🎯 Target Language"],
        "ru": ["🔄 Перевести", "❔ Помощь", "🌐 Изменить язык", "📋 История", "🎯 Целевой язык"]
    }
    
    texts = button_text.get(lang_code, button_text["en"])
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts[0], callback_data="translate"),
                InlineKeyboardButton(text=texts[1], callback_data="help")
            ],
            [
                InlineKeyboardButton(text=texts[2], callback_data="setlanguage"),
                InlineKeyboardButton(text=texts[3], callback_data="history")
            ],
            [
                InlineKeyboardButton(text=texts[4], callback_data="set_target_language")
            ]
        ]
    )

def choose_language_keyboard(languages: Dict, lang_code="en", action_prefix="lang", page=0, page_size=8):
    """
    Создает клавиатуру для выбора языка перевода с пагинацией
    
    :param languages: Словарь доступных языков {code: name}
    :param lang_code: Код языка интерфейса
    :param action_prefix: Префикс для callback_data
    :param page: Текущая страница
    :param page_size: Количество языков на странице
    :return: InlineKeyboardMarkup
    """
    # Сортируем языки по названию
    sorted_languages = sorted(languages.items(), key=lambda x: x[1])
    
    # Рассчитываем общее количество страниц
    total_pages = (len(sorted_languages) + page_size - 1) // page_size
    
    # Получаем языки для текущей страницы
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(sorted_languages))
    current_page_languages = sorted_languages[start_idx:end_idx]
    
    # Создаем кнопки, по 2 в каждом ряду
    keyboard = []
    row = []
    
    for i, (code, name) in enumerate(current_page_languages):
        # Добавляем кнопку с названием языка
        row.append(InlineKeyboardButton(
            text=name, 
            callback_data=f"{action_prefix}_{code}"
        ))
        
        # После каждой второй кнопки или в конце списка добавляем новый ряд
        if len(row) == 2 or i == len(current_page_languages) - 1:
            keyboard.append(row.copy())
            row = []
    
    # Добавляем навигационные кнопки
    nav_row = []
    
    # Добавляем кнопку "Предыдущая страница" если не на первой странице
    if page > 0:
        prev_text = "◀️ Prev" if lang_code == "en" else "◀️ Назад"
        nav_row.append(InlineKeyboardButton(
            text=prev_text,
            callback_data=f"page_{action_prefix}_{page-1}"
        ))
    
    # Добавляем информацию о текущей странице
    page_text = f"{page+1}/{total_pages}"
    nav_row.append(InlineKeyboardButton(
        text=page_text,
        callback_data="noop"  # Это кнопка не выполняет никаких действий
    ))
    
    # Добавляем кнопку "Следующая страница" если не на последней странице
    if page < total_pages - 1:
        next_text = "Next ▶️" if lang_code == "en" else "Далее ▶️"
        nav_row.append(InlineKeyboardButton(
            text=next_text,
            callback_data=f"page_{action_prefix}_{page+1}"
        ))
    
    # Добавляем навигационные кнопки в клавиатуру
    if total_pages > 1:
        keyboard.append(nav_row)
    
    # Добавляем нижний ряд с кнопками отмены и главного меню
    bottom_row = []
    
    # Кнопка отмены
    cancel_text = "❌ Cancel" if lang_code == "en" else "❌ Отмена"
    bottom_row.append(InlineKeyboardButton(text=cancel_text, callback_data="cancel"))
    
    # Кнопка главного меню
    menu_text = "🏠 Main Menu" if lang_code == "en" else "🏠 Главное меню"
    bottom_row.append(InlineKeyboardButton(text=menu_text, callback_data="main_menu"))
    
    keyboard.append(bottom_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def after_translation_keyboard(lang_code="en"):
    """
    Создает клавиатуру после перевода с опциями "Перевести ещё" и "Назад в меню"
    """
    from utils.formatters import get_message
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_message(lang_code, "translate_again"), 
                    callback_data="translate_again"
                ),
                InlineKeyboardButton(
                    text=get_message(lang_code, "back_to_menu"), 
                    callback_data="main_menu"
                )
            ]
        ]
    )

def history_keyboard(lang_code="en"):
    """
    Создает inline-клавиатуру для истории переводов
    """
    button_text = {
        "en": ["🧹 Clear History", "❌ Close", "🏠 Main Menu"],
        "ru": ["🧹 Очистить историю", "❌ Закрыть", "🏠 Главное меню"]
    }
    
    texts = button_text.get(lang_code, button_text["en"])
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts[0], callback_data="clear_history"),
                InlineKeyboardButton(text=texts[1], callback_data="close")
            ],
            [
                InlineKeyboardButton(text=texts[2], callback_data="main_menu")
            ]
        ]
    )

def target_language_keyboard(languages: Dict, lang_code="en", page=0, page_size=8):
    """
    Создает клавиатуру для выбора целевого языка перевода с пагинацией
    
    :param languages: Словарь доступных языков {code: name}
    :param lang_code: Код языка интерфейса
    :param page: Текущая страница
    :param page_size: Количество языков на странице
    :return: InlineKeyboardMarkup
    """
    # Сортируем языки по названию
    sorted_languages = sorted(languages.items(), key=lambda x: x[1])
    
    # Рассчитываем общее количество страниц
    total_pages = (len(sorted_languages) + page_size - 1) // page_size
    
    # Получаем языки для текущей страницы
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(sorted_languages))
    current_page_languages = sorted_languages[start_idx:end_idx]
    
    # Создаем кнопки, по 2 в каждом ряду
    keyboard = []
    row = []
    
    for i, (code, name) in enumerate(current_page_languages):
        # Добавляем кнопку с названием языка
        row.append(InlineKeyboardButton(
            text=name, 
            callback_data=f"target_{code}"
        ))
        
        # После каждой второй кнопки или в конце списка добавляем новый ряд
        if len(row) == 2 or i == len(current_page_languages) - 1:
            keyboard.append(row.copy())
            row = []
    
    # Добавляем навигационные кнопки
    nav_row = []
    
    # Добавляем кнопку "Предыдущая страница" если не на первой странице
    if page > 0:
        prev_text = "◀️ Prev" if lang_code == "en" else "◀️ Назад"
        nav_row.append(InlineKeyboardButton(
            text=prev_text,
            callback_data=f"page_target_{page-1}"
        ))
    
    # Добавляем информацию о текущей странице
    page_text = f"{page+1}/{total_pages}"
    nav_row.append(InlineKeyboardButton(
        text=page_text,
        callback_data="noop"  # Это кнопка не выполняет никаких действий
    ))
    
    # Добавляем кнопку "Следующая страница" если не на последней странице
    if page < total_pages - 1:
        next_text = "Next ▶️" if lang_code == "en" else "Далее ▶️"
        nav_row.append(InlineKeyboardButton(
            text=next_text,
            callback_data=f"page_target_{page+1}"
        ))
    
    # Добавляем навигационные кнопки в клавиатуру
    if total_pages > 1:
        keyboard.append(nav_row)
    
    # Добавляем нижний ряд с кнопками отмены и главного меню
    bottom_row = []
    
    # Кнопка отмены
    cancel_text = "❌ Cancel" if lang_code == "en" else "❌ Отмена"
    bottom_row.append(InlineKeyboardButton(text=cancel_text, callback_data="cancel"))
    
    # Кнопка главного меню
    menu_text = "🏠 Main Menu" if lang_code == "en" else "🏠 Главное меню"
    bottom_row.append(InlineKeyboardButton(text=menu_text, callback_data="main_menu"))
    
    keyboard.append(bottom_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)