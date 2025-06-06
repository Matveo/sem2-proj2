from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.language_state import LanguageState
from utils.formatters import get_message, get_user_language, set_user_language, set_user_translate_languages
from utils.logger import logger
from keyboards.inline import choose_language_keyboard, main_menu_inline_keyboard, target_language_keyboard
from services.api_client import get_languages

router = Router()

# Обработчик команды setlanguage и callback_data "setlanguage"
@router.message(Command("setlanguage"))
async def cmd_setlanguage(message: Message, state: FSMContext):
    """
    Обработчик команды /setlanguage
    Переводит в состояние выбора языка интерфейса
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /setlanguage")
    
    # Отправляем сообщение с предложением выбрать язык
    language_msg = get_message(user_lang, "setlanguage_message")
    
    # Создаем простую клавиатуру для выбора языка интерфейса
    # Для этого используем словарь с доступными языками интерфейса
    interface_languages = {
        "en": "English",
        "ru": "Русский"
    }
    
    # Устанавливаем состояние выбора языка
    await state.set_state(LanguageState.waiting_for_language)
    
    await message.answer(
        language_msg,
        reply_markup=choose_language_keyboard(interface_languages, user_lang, "interface")
    )


@router.callback_query(F.data == "setlanguage")
async def callback_setlanguage(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Language" в inline клавиатуре
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    
    # Отправляем сообщение с предложением выбрать язык
    language_msg = get_message(user_lang, "setlanguage_message")
    
    # Создаем простую клавиатуру для выбора языка интерфейса
    interface_languages = {
        "en": "English",
        "ru": "Русский"
    }
    
    # Устанавливаем состояние выбора языка
    await state.set_state(LanguageState.waiting_for_language)
    
    await callback.message.edit_text(
        language_msg,
        reply_markup=choose_language_keyboard(interface_languages, user_lang, "interface")
    )
    await callback.answer()


# Обработчик выбора языка интерфейса
@router.callback_query(F.data.startswith("interface_"))
async def set_interface_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора языка интерфейса из inline клавиатуры
    """
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    # Извлекаем код языка из callback_data
    language_code = callback.data.split("_")[1]
    
    logger.info(f"Пользователь {username} (ID: {user_id}) выбрал язык интерфейса: {language_code}")
    
    # Сохраняем выбранный язык в настройках пользователя
    if set_user_language(user_id, language_code):
        # Получаем сообщение на новом языке
        success_msg = get_message(language_code, "language_chosen")
        
        await callback.message.edit_text(
            success_msg,
            reply_markup=main_menu_inline_keyboard(language_code)
        )
    else:
        # Если произошла ошибка при сохранении
        error_msg = get_message(language_code, "language_set_error")
        await callback.message.edit_text(
            error_msg,
            reply_markup=main_menu_inline_keyboard(language_code)
        )
    
    # Очищаем состояние FSM
    await state.clear()
    await callback.answer()


# Обработчик пагинации для языков интерфейса
@router.callback_query(F.data.startswith("page_interface_"))
async def page_interface_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик пагинации для выбора языка интерфейса
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    
    # Извлекаем номер страницы
    page = int(callback.data.split("_")[2])
    
    # Создаем словарь с доступными языками интерфейса
    interface_languages = {
        "en": "English",
        "ru": "Русский"
    }
    
    await callback.message.edit_text(
        get_message(user_lang, "setlanguage_message"),
        reply_markup=choose_language_keyboard(interface_languages, user_lang, "interface", page)
    )
    await callback.answer()


# Обработчик отмены
@router.callback_query(F.data == "cancel")
async def cancel_language_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик отмены выбора языка
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    
    # Очищаем состояние FSM
    await state.clear()
    
    # Отправляем сообщение об отмене
    cancel_text = get_message(user_lang, "operation_cancelled")
    
    # Редактируем сообщение, чтобы убрать клавиатуру
    await callback.message.edit_text(
        cancel_text,
        reply_markup=main_menu_inline_keyboard(user_lang)
    )
    
    await callback.answer()
