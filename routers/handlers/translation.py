from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from states.language_state import TranslateState
from utils.formatters import get_message, get_user_language, get_user_translate_languages, set_user_translate_languages
from utils.logger import logger
from keyboards.inline import main_menu_inline_keyboard, after_translation_keyboard, target_language_keyboard
from services.api_client import translate_text, get_languages
from services.history_storage import add_to_history

def check_user_banned(user_id: int) -> bool:
    """Проверяет, заблокирован ли пользователь"""
    try:
        from routers.handlers.admin import is_user_banned
        return is_user_banned(user_id)
    except ImportError:
        return False

router = Router()

# Обработчик команды translate и callback_data "translate"
@router.message(Command("translate"))
async def cmd_translate(message: Message, state: FSMContext):
    """
    Обработчик команды /translate
    Переводит в состояние ожидания текста для перевода
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    user_lang = get_user_language(user_id)
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await message.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.")
        return
    
    logger.info(f"Пользователь {username} (ID: {user_id}) отправил команду /translate")
    
    # Получаем текст сообщения для команды translate
    translate_msg = get_message(user_lang, "translate_message")
    
    # Сохраняем в состояние язык пользователя для дальнейшего использования
    await state.update_data(user_lang=user_lang)
    
    # Устанавливаем состояние waiting_for_text
    await state.set_state(TranslateState.waiting_for_text)
    
    # Отправляем сообщение с инструкцией
    await message.answer(translate_msg)


@router.callback_query(F.data == "translate")
async def callback_translate(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Translate" в inline клавиатуре
    """
    user_id = callback.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await callback.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.", show_alert=True)
        return
    
    user_lang = get_user_language(user_id)
    translate_msg = get_message(user_lang, "translate_message")
    
    # Устанавливаем состояние waiting_for_text
    await state.set_state(TranslateState.waiting_for_text)
    await state.update_data(user_lang=user_lang)
    
    # Отправляем сообщение и удаляем уведомление о нажатии кнопки
    await callback.message.answer(translate_msg)
    await callback.answer()


@router.message(TranslateState.waiting_for_text)
async def process_translation(message: Message, state: FSMContext):
    """
    Обработчик текста для перевода в состоянии waiting_for_text
    """
    user_id = message.from_user.id
    text = message.text
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await message.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.")
        await state.clear()
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    user_lang = data.get("user_lang", "en")
    
    # Всегда используем автоопределение для исходного языка
    source_lang = "auto"
    
    # Получаем целевой язык из настроек пользователя, по умолчанию - английский
    translate_settings = get_user_translate_languages(user_id)
    target_lang = translate_settings["target"]
    
    # Отправляем сообщение о процессе перевода
    processing_msg = await message.answer(get_message(user_lang, "processing"))
    try:
        # Переводим текст
        translated = await translate_text(text, source_lang, target_lang)
        
        if translated:
            # Определяем, какой язык был определен автоматически
            detected_lang = "auto" # В реальном API здесь будет определенный язык
            
            # Формируем сообщение с переводом
            translation_result = (
                f"<b>{text}</b>\n\n"
                f"🔄 AUTO ➡️ {target_lang.upper()}\n\n"
                f"{translated}"
            )
            
            # Добавляем запись в историю
            history_record = {
                "original": text,
                "translated": translated,
                "from_lang": "auto",
                "to_lang": target_lang
            }
            add_to_history(user_id, history_record)
            
            # Удаляем сообщение о процессе перевода
            await processing_msg.delete()
            
            # Выходим из машины состояний
            await state.clear()
            
            # Отправляем результат перевода с клавиатурой действий
            await message.answer(
                translation_result,
                reply_markup=after_translation_keyboard(user_lang)
            )
        else:
            # Если перевод не удался
            await processing_msg.delete()
            # Используем сообщение на языке пользователя
            error_message = get_message(user_lang, "translation_error") 
            await message.answer(
                error_message,
                reply_markup=main_menu_inline_keyboard(user_lang)
            )
            await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        await processing_msg.delete()
        await message.answer(
            get_message(user_lang, "api_error"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )
        await state.clear()


@router.callback_query(F.data == "set_target_language")
async def set_target_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку выбора целевого языка перевода
    """
    user_id = callback.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await callback.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.", show_alert=True)
        return
    
    user_lang = get_user_language(user_id)
    
    # Получаем доступные языки
    languages = await get_languages()
    
    if languages:
        # Отправляем клавиатуру выбора целевого языка
        await callback.message.edit_text(
            get_message(user_lang, "select_target_language"),
            reply_markup=target_language_keyboard(languages, user_lang)
        )
    else:
        # Если не удалось получить языки
        await callback.message.edit_text(
            get_message(user_lang, "translation_error"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )
    
    await callback.answer()


@router.callback_query(F.data == "close")
async def close_message(callback: CallbackQuery):
    """
    Закрывает сообщение при нажатии на кнопку Закрыть
    """
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("target_"))
async def select_target_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора целевого языка для перевода
    """
    user_id = callback.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await callback.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.", show_alert=True)
        return
    
    user_lang = get_user_language(user_id)
    
    # Извлекаем код языка из callback_data
    lang_code = callback.data.replace("target_", "")
      # Сохраняем выбранный целевой язык
    set_user_translate_languages(user_id, source="auto", target=lang_code)
    
    # Получаем название языка для отображения
    languages = await get_languages()
    lang_name = "Unknown"
    if languages and lang_code in languages:
        lang_name = languages[lang_code]
    
    # Формируем сообщение об успешном сохранении
    success_message = get_message(user_lang, "target_language_set").format(language=lang_name)
    
    # Обновляем сообщение
    await callback.message.edit_text(
        success_message,
        reply_markup=main_menu_inline_keyboard(user_lang)
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("page_target_"))
async def navigate_target_languages(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик навигации по страницам при выборе целевого языка
    """
    user_id = callback.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await callback.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.", show_alert=True)
        return
    
    user_lang = get_user_language(user_id)
    
    # Извлекаем номер страницы из callback_data
    page = int(callback.data.replace("page_target_", ""))
    logger.info(f"navigate_target_languages: user_id={user_id}, page={page}")
    
    # Получаем доступные языки
    languages = await get_languages()
    
    if languages:
        # Обновляем клавиатуру с новой страницей
        await callback.message.edit_reply_markup(
            reply_markup=target_language_keyboard(languages, user_lang, page=page)
        )
    else:
        # Если не удалось получить языки
        await callback.message.edit_text(
            get_message(user_lang, "translation_error"),
            reply_markup=main_menu_inline_keyboard(user_lang)
        )
    
    await callback.answer()


@router.callback_query(F.data == "translate_again")
async def callback_translate_again(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Перевести ещё"
    """
    user_id = callback.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await callback.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.", show_alert=True)
        return
    
    user_lang = get_user_language(user_id)
    translate_msg = get_message(user_lang, "translate_prompt")
    
    # Устанавливаем состояние waiting_for_text
    await state.set_state(TranslateState.waiting_for_text)
    await state.update_data(user_lang=user_lang)
    
    # Отправляем сообщение и удаляем уведомление о нажатии кнопки
    await callback.message.edit_text(translate_msg)
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Главное меню"
    """
    user_id = callback.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if check_user_banned(user_id):
        await callback.answer("🚫 You have been banned from using this bot. / Вы заблокированы и не можете использовать этого бота.", show_alert=True)
        return
    
    user_lang = get_user_language(user_id)
    
    # Очищаем состояние
    await state.clear()
    
    # Отправляем главное меню
    await callback.message.edit_text(
        get_message(user_lang, "select_action"),
        reply_markup=main_menu_inline_keyboard(user_lang)
    )
    await callback.answer()