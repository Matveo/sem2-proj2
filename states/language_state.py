from aiogram.fsm.state import StatesGroup, State

class TranslateState(StatesGroup):
    """
    Состояния для процесса перевода текста
    """
    waiting_for_text = State()  # Ожидание ввода текста для перевода


class LanguageState(StatesGroup):
    """
    Состояния для процесса выбора языка
    """
    waiting_for_language = State()  # Ожидание выбора языка интерфейса