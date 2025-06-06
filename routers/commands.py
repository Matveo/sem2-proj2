from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import json
import os

from states.language_state import LanguageState
from utils.logger import logger
from utils.formatters import get_message, get_user_language, format_translation_history, set_user_language, get_user_translate_languages
from keyboards.inline import help_inline_keyboard, about_inline_keyboard, main_menu_inline_keyboard, history_keyboard, choose_language_keyboard
from services.api_client import translate_text, get_languages
from services.history_storage import add_to_history, get_history, clear_history

def check_user_banned(user_id: int) -> bool:
    """Проверяет, заблокирован ли пользователь"""
    try:
        from routers.handlers.admin import is_user_banned
        return is_user_banned(user_id)
    except ImportError:
        return False

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await message.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.")
        return
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /start")
    
    start_text = get_message(user_lang, "start_message")
    
    await message.answer(
        start_text,
        reply_markup=main_menu_inline_keyboard(user_lang)
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await message.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.")
        return
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /help")
    
    help_text = get_message(user_lang, "help_message")
    
    await message.answer(
        help_text,
        reply_markup=help_inline_keyboard()
    )


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Help"
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    help_text = get_message(user_lang, "help_message")
    
    # Очищаем состояние если оно есть
    await state.clear()
    
    await callback.message.edit_text(
        help_text,
        reply_markup=help_inline_keyboard(user_lang)
    )
    await callback.answer()


@router.message(Command("translate"))
async def cmd_translate(message: Message):
    """
    Обработчик команды /translate
    Заглушка для FSM - пока делаем простой перевод с английского на русский
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /translate")
    translate_text_msg = get_message(user_lang, "translate_message")
    example_msg = get_message(user_lang, "translate_example")
    
    await message.answer(f"{translate_text_msg}\n\n{example_msg}")

@router.message(Command("setlanguage"))
async def cmd_setlanguage(message: Message):
    """
    Обработчик команды /setlanguage
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /setlanguage")
    
    setlang_text = get_message(user_lang, "setlanguage_message")
    await message.answer(
        setlang_text,
        reply_markup=main_menu_inline_keyboard(user_lang)
    )

@router.message(Command("history"))
async def cmd_history(message: Message):
    """
    Обработчик команды /history
    Показывает последние 5 переводов пользователя
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /history")
    
    user_history = get_history(user_id, limit=5)
    
    if user_history:
        history_text = get_message(user_lang, "history_message") + "\n\n"
        for i, translation in enumerate(user_history, 1):
            from_lang = translation.get('from_lang', translation.get('from', 'неизв.'))
            to_lang = translation.get('to_lang', translation.get('to', 'неизв.'))
            timestamp = translation.get('timestamp', '')
            
            # Форматируем дату если есть
            date_str = ""
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    date_str = f" ({dt.strftime('%d.%m %H:%M')})"
                except:
                    pass
            
            history_text += f"{i}. 🔄 {from_lang}→{to_lang}{date_str}\n"
            history_text += f"   📝 {translation['original']}\n"
            history_text += f"   ✅ {translation['translated']}\n\n"    
    else:
        history_text = get_message(user_lang, "no_history")
    
    await message.answer(history_text)

@router.message(Command("clear_history"))
async def cmd_clear_history(message: Message):
    """
    Обработчик команды /clear_history
    Очищает историю переводов пользователя
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /clear_history")
    
    if clear_history(user_id):
        await message.answer(
            get_message(user_lang, "history_cleared"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )
    else:
        await message.answer(
            get_message(user_lang, "history_clear_error"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )

# Обработчики для reply-кнопок выбора языка
@router.message(F.text == "English")
async def language_english(message: Message):
    """
    Обработчик выбора английского языка
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"Пользователь {username} (ID: {user_id}) выбрал английский язык")
    
    # Устанавливаем язык пользователя
    set_user_language(user_id, "en")
    
    await message.answer(
        get_message("en", "language_set"),
        reply_markup=main_menu_inline_keyboard("en")
    )

@router.message(F.text == "Русский")
async def language_russian(message: Message):
    """
    Обработчик выбора русского языка
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"Пользователь {username} (ID: {user_id}) выбрал русский язык")
    
    # Устанавливаем язык пользователя
    set_user_language(user_id, "ru")
    
    await message.answer(
        get_message("ru", "language_set"),
        reply_markup=main_menu_inline_keyboard("ru")
    )

# Обработчик для любого текстового сообщения (автоперевод)
@router.message(F.text & ~F.text.startswith('/'))
async def handle_text_translation(message: Message):
    """
    Обработчик для автоматического перевода текстовых сообщений
    Всегда использует автоопределение языка и целевой язык из настроек пользователя
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    text = message.text
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await message.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.")
        return
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил текст для перевода: '{text[:50]}...'")
    
    # Всегда используем автоопределение языка источника
    source_lang = "auto"
      # Получаем целевой язык из настроек пользователя
    translate_settings = get_user_translate_languages(user_id)
    target_lang = translate_settings["target"]
    
    # Получаем язык пользователя для сообщений
    user_lang = get_user_language(user_id)
    
    # Отправляем сообщение о начале перевода
    processing_msg = await message.answer(get_message(user_lang, "processing"))
    
    try:
        # Вызываем API для перевода
        translated = await translate_text(text, source_lang, target_lang)
        if translated:
            # Формируем ответ
            response_text = f"🔄 {source_lang.upper()} → {target_lang.upper()}\n\n"
            response_text += f"{get_message(user_lang, 'original_text')}\n{text}\n\n"
            response_text += f"{get_message(user_lang, 'translated_text')}\n{translated}"
            
            # Сохраняем в историю
            history_record = {
                "original": text,
                "translated": translated,
                "from_lang": source_lang,
                "to_lang": target_lang
            }
            
            add_to_history(user_id, history_record)
            logger.info(f"Перевод сохранён в историю пользователя {user_id}")
            
            # Удаляем сообщение о процессе и отправляем результат
            await processing_msg.delete()
            await message.answer(response_text, parse_mode="HTML")
            
        else:
            # Если перевод не удался, используем локализованное сообщение об ошибке
            await processing_msg.delete()
            await message.answer(
                get_message(user_lang, "translation_error"),
                reply_markup=main_menu_inline_keyboard(user_lang)
            )
            
    except Exception as e:
        logger.error(f"Ошибка при переводе: {e}")
        await processing_msg.delete()
        await message.answer(
            get_message(user_lang, "api_error"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )

@router.callback_query(F.data == "translate")
async def callback_translate(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик inline-кнопки "Translate"
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    await callback.message.edit_text(
        get_message(user_lang, "translate_message"),
        reply_markup=main_menu_inline_keyboard(user_lang)
    )
    await callback.answer()

@router.callback_query(F.data == "history")
async def callback_history(callback: CallbackQuery):
    """
    Обработчик inline-кнопки "History"
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    user_history = get_history(user_id, limit=5)
    
    if user_history:
        history_text = format_translation_history(user_history, user_lang)
    else:
        history_text = get_message(user_lang, "no_history")
    
    await callback.message.edit_text(
        history_text,
        reply_markup=history_keyboard(user_lang)
    )
    await callback.answer()

@router.callback_query(F.data == "about")
async def callback_about(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "About"
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    
    about_text = "🤖 Translator Bot v1.0\n\nThis bot can translate text between different languages using AI translation services.\n\nDeveloped with aiogram 3 and Python."
    if user_lang == "ru":
        about_text = "🤖 Бот-переводчик v1.0\n\nЭтот бот может переводить текст между различными языками, используя AI-сервисы перевода.\n\nРазработан с использованием aiogram 3 и Python."
    
    # Очищаем состояние если оно есть
    await state.clear()
    
    await callback.message.edit_text(
        about_text,
        reply_markup=about_inline_keyboard(user_lang)
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Main Menu"
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    
    # Очищаем состояние если оно есть
    await state.clear()
    
    # Отправляем главное меню
    await callback.message.edit_text(
        get_message(user_lang, "select_action"),
        reply_markup=main_menu_inline_keyboard(user_lang)
    )
    await callback.answer()

@router.callback_query(F.data == "clear_history")
async def callback_clear_history(callback: CallbackQuery):
    """
    Обработчик кнопки очистки истории
    """
    user_id = callback.from_user.id
    user_lang = get_user_language(user_id)
    
    if clear_history(user_id):
        await callback.message.edit_text(
            get_message(user_lang, "history_cleared"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )
    else:
        await callback.message.edit_text(
            get_message(user_lang, "history_clear_error"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )
    await callback.answer()

@router.callback_query(F.data == "close")
async def callback_close(callback: CallbackQuery):
    """
    Обработчик кнопки закрытия
    """
    await callback.message.delete()
    await callback.answer()