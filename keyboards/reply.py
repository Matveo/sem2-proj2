from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def language_keyboard():
    """
    Создает reply-клавиатуру для выбора языка
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="English")],
            [KeyboardButton(text="Русский")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_menu_keyboard():
    """
    Создает основную reply-клавиатуру с командами
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/translate"), KeyboardButton(text="/help")],
            [KeyboardButton(text="/setlanguage"), KeyboardButton(text="/history")]
        ],
        resize_keyboard=True
    )