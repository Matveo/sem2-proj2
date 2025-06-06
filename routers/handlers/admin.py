"""
Обработчики команд админ-панели
"""

import json
import os
from typing import List, Dict, Any

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from filters.admin_filter import IsAdmin, IsAdminCallback, IsNotAdmin
from states.admin_states import AdminStates
from utils.logger import logger
from utils.formatters import get_user_language, get_message, USER_SETTINGS
from config.settings import HISTORY_FILE
from services.history_storage import load_history

router = Router()

# Файл для хранения заблокированных пользователей
BANNED_USERS_FILE = "storage/banned_users.json"

def load_banned_users() -> List[int]:
    """Загружает список заблокированных пользователей"""
    try:
        if os.path.exists(BANNED_USERS_FILE):
            with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки списка заблокированных пользователей: {e}")
    return []

def save_banned_users(banned_users: List[int]) -> None:
    """Сохраняет список заблокированных пользователей"""
    try:
        os.makedirs(os.path.dirname(BANNED_USERS_FILE), exist_ok=True)
        with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(banned_users, f, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения списка заблокированных пользователей: {e}")

def get_all_users() -> List[int]:
    """Получает список всех пользователей из истории"""
    try:
        history = load_history()
        user_ids = set()
        
        # История хранится в формате {user_id_str: [...]}
        for user_id_str in history.keys():
            try:
                user_ids.add(int(user_id_str))
            except ValueError:
                continue
        
        return list(user_ids)
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        return []

def get_admin_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Создает клавиатуру админ-панели"""
    buttons = [
        [InlineKeyboardButton(
            text=get_message(lang, "admin_stats"),
            callback_data="admin_stats"
        )],
        [InlineKeyboardButton(
            text=get_message(lang, "admin_broadcast"),
            callback_data="admin_broadcast"
        )],
        [InlineKeyboardButton(
            text=get_message(lang, "admin_ban"),
            callback_data="admin_ban"
        )],
        [InlineKeyboardButton(
            text=get_message(lang, "admin_unban"),
            callback_data="admin_unban"
        )],
        [InlineKeyboardButton(
            text=get_message(lang, "admin_banned_list"),
            callback_data="admin_banned_list"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard(lang: str = "en", confirm_data: str = "confirm", cancel_data: str = "cancel") -> InlineKeyboardMarkup:
    """Создает клавиатуру подтверждения"""
    buttons = [
        [
            InlineKeyboardButton(
                text=get_message(lang, "admin_confirm"),
                callback_data=confirm_data
            ),
            InlineKeyboardButton(
                text=get_message(lang, "admin_cancel"),
                callback_data=cancel_data
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Главная админ-панель
@router.message(Command("admin"), IsAdmin())
async def admin_panel(message: Message):
    """Обработчик главной админ-панели"""
    try:
        user_lang = get_user_language(message.from_user.id)
        logger.info(f"Открытие админ-панели пользователем {message.from_user.id}")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message(user_lang, "admin_stats"), callback_data="admin_stats")],
            [InlineKeyboardButton(text=get_message(user_lang, "admin_broadcast"), callback_data="admin_broadcast")],
            [InlineKeyboardButton(text=get_message(user_lang, "admin_ban"), callback_data="admin_ban")],
            [InlineKeyboardButton(text=get_message(user_lang, "admin_unban"), callback_data="admin_unban")],
            [InlineKeyboardButton(text=get_message(user_lang, "admin_banned_list"), callback_data="admin_banned_list")]
        ])
        
        await message.answer(
            get_message(user_lang, "admin_panel_welcome"),
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка в admin_panel: {e}")
        await message.answer("Ошибка при открытии админ-панели")

# Статистика
@router.message(Command("stats"), IsAdmin())
@router.callback_query(F.data == "admin_stats", IsAdminCallback())
async def admin_stats(event):
    """Показывает статистику бота"""
    if isinstance(event, Message):
        user_id = event.from_user.id
        answer_func = event.answer
    else:  # CallbackQuery
        user_id = event.from_user.id
        answer_func = event.message.edit_text
    await event.answer()
    
    user_lang = get_user_language(user_id)
    
    try:
        # Получаем статистику пользователей
        total_users = len(USER_SETTINGS)
        
        # Получаем общее количество переводов
        history = load_history()
        total_translations = sum(len(user_history) for user_history in history.values())
        
        # Получаем количество заблокированных пользователей
        banned_users = load_banned_users()
        total_banned = len(banned_users)
        stats_text = get_message(user_lang, "admin_stats_text").format(
            total_users=total_users,
            total_translations=total_translations,
            banned_users=total_banned
        )
        
        await answer_func(
            stats_text,
            reply_markup=get_admin_keyboard(user_lang)
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await answer_func(
            get_message(user_lang, "admin_error"),
            reply_markup=get_admin_keyboard(user_lang)
        )

# Рассылка - начало
@router.message(Command("broadcast"), IsAdmin())
@router.callback_query(F.data == "admin_broadcast", IsAdminCallback())
async def admin_broadcast_start(event, state: FSMContext):
    """Начинает процесс рассылки"""
    if isinstance(event, Message):
        user_id = event.from_user.id
        answer_func = event.answer
    else:  # CallbackQuery
        user_id = event.from_user.id
        answer_func = event.message.edit_text
        await event.answer()
    
    user_lang = get_user_language(user_id)
    
    await state.set_state(AdminStates.broadcast_waiting_message)
    await answer_func(get_message(user_lang, "admin_broadcast_enter_message"))

@router.message(AdminStates.broadcast_waiting_message, IsAdmin())
async def admin_broadcast_message(message: Message, state: FSMContext):
    """Получает сообщение для рассылки и запрашивает подтверждение"""
    user_lang = get_user_language(message.from_user.id)
    
    # Сохраняем сообщение
    await state.update_data(broadcast_message=message.text)
    await state.set_state(AdminStates.broadcast_waiting_confirmation)
    
    all_users = get_all_users()
    banned_users = load_banned_users()
    active_users = len([u for u in all_users if u not in banned_users])
    preview_text = get_message(user_lang, "admin_broadcast_preview").format(
        message=message.text,
        user_count=active_users
    )
    
    await message.answer(
        preview_text,
        reply_markup=get_confirmation_keyboard(user_lang, "broadcast_confirm", "broadcast_cancel")
    )

@router.callback_query(F.data == "broadcast_confirm", IsAdminCallback())
async def admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot):
    """Выполняет рассылку"""
    user_lang = get_user_language(callback.from_user.id)
    
    data = await state.get_data()
    broadcast_message = data.get('broadcast_message')
    if not broadcast_message:
        await callback.message.edit_text(get_message(user_lang, "admin_error"))
        await state.clear()
        return
    
    await callback.answer()
    await callback.message.edit_text(get_message(user_lang, "admin_broadcast_starting"))
    
    all_users = get_all_users()
    banned_users = load_banned_users()
    active_users = [u for u in all_users if u not in banned_users]
    
    success_count = 0
    error_count = 0
    
    for user_id in active_users:
        try:
            await bot.send_message(user_id, broadcast_message)
            success_count += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            error_count += 1
    result_text = get_message(user_lang, "admin_broadcast_result").format(
        success=success_count,
        errors=error_count
    )
    
    await callback.message.edit_text(
        result_text,
        reply_markup=get_admin_keyboard(user_lang)
    )
    
    await state.clear()

@router.callback_query(F.data == "broadcast_cancel", IsAdminCallback())
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменяет рассылку"""
    user_lang = get_user_language(callback.from_user.id)
    
    await callback.answer()
    await callback.message.edit_text(
        get_message(user_lang, "admin_broadcast_cancelled"),
        reply_markup=get_admin_keyboard(user_lang)
    )
    await state.clear()

# Блокировка пользователя
@router.message(Command("ban"), IsAdmin())
@router.callback_query(F.data == "admin_ban", IsAdminCallback())
async def admin_ban_start(event, state: FSMContext):
    """Начинает процесс блокировки пользователя"""
    if isinstance(event, Message):
        user_id = event.from_user.id
        answer_func = event.answer
    else:  # CallbackQuery
        user_id = event.from_user.id
        answer_func = event.message.edit_text
        await event.answer()
    
    user_lang = get_user_language(user_id)
    
    await state.set_state(AdminStates.ban_waiting_user_id)
    await answer_func(get_message(user_lang, "admin_ban_enter_user_id"))

@router.message(AdminStates.ban_waiting_user_id, IsAdmin())
async def admin_ban_user_id(message: Message, state: FSMContext):
    """Получает ID пользователя для блокировки"""
    user_lang = get_user_language(message.from_user.id)
    
    try:
        user_id_to_ban = int(message.text.strip())
        
        # Проверяем, не пытается ли админ заблокировать сам себя
        if user_id_to_ban == message.from_user.id:
            await message.answer(get_message(user_lang, "admin_ban_self_error"))
            return
        
        # Проверяем, не заблокирован ли уже пользователь
        banned_users = load_banned_users()
        if user_id_to_ban in banned_users:
            await message.answer(get_message(user_lang, "admin_ban_already_banned"))
            return
        
        await state.update_data(user_id_to_ban=user_id_to_ban)
        await state.set_state(AdminStates.ban_waiting_confirmation)
        
        confirm_text = get_message(user_lang, "admin_ban_confirm").format(user_id=user_id_to_ban)
        
        await message.answer(
            confirm_text,
            reply_markup=get_confirmation_keyboard(user_lang, "ban_confirm", "ban_cancel")
        )
        
    except ValueError:
        await message.answer(get_message(user_lang, "admin_ban_invalid_id"))

@router.callback_query(F.data == "ban_confirm", IsAdminCallback())
async def admin_ban_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждает блокировку пользователя"""
    user_lang = get_user_language(callback.from_user.id)
    
    data = await state.get_data()
    user_id_to_ban = data.get('user_id_to_ban')
    
    if not user_id_to_ban:
        await callback.message.edit_text(get_message(user_lang, "admin_error"))
        await state.clear()
        return
    
    banned_users = load_banned_users()
    banned_users.append(user_id_to_ban)
    save_banned_users(banned_users)
    
    await callback.answer()
    await callback.message.edit_text(
        get_message(user_lang, "admin_ban_success").format(user_id=user_id_to_ban),
        reply_markup=get_admin_keyboard(user_lang)
    )
    
    logger.info(f"Админ {callback.from_user.id} заблокировал пользователя {user_id_to_ban}")
    await state.clear()

@router.callback_query(F.data == "ban_cancel", IsAdminCallback())
async def admin_ban_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменяет блокировку пользователя"""
    user_lang = get_user_language(callback.from_user.id)
    
    await callback.answer()
    await callback.message.edit_text(
        get_message(user_lang, "admin_ban_cancelled"),
        reply_markup=get_admin_keyboard(user_lang)
    )
    await state.clear()

# Разблокировка пользователя
@router.message(Command("unban"), IsAdmin())
@router.callback_query(F.data == "admin_unban", IsAdminCallback())
async def admin_unban_start(event, state: FSMContext):
    """Начинает процесс разблокировки пользователя"""
    if isinstance(event, Message):
        user_id = event.from_user.id
        answer_func = event.answer
    else:  # CallbackQuery
        user_id = event.from_user.id
        answer_func = event.message.edit_text
        await event.answer()
    
    user_lang = get_user_language(user_id)
    
    await state.set_state(AdminStates.unban_waiting_user_id)
    await answer_func(get_message(user_lang, "admin_unban_enter_user_id"))

@router.message(AdminStates.unban_waiting_user_id, IsAdmin())
async def admin_unban_user_id(message: Message, state: FSMContext):
    """Получает ID пользователя для разблокировки"""
    user_lang = get_user_language(message.from_user.id)
    
    try:
        user_id_to_unban = int(message.text.strip())
        
        # Проверяем, заблокирован ли пользователь
        banned_users = load_banned_users()
        if user_id_to_unban not in banned_users:
            await message.answer(get_message(user_lang, "admin_unban_not_banned"))
            return
        
        await state.update_data(user_id_to_unban=user_id_to_unban)
        await state.set_state(AdminStates.unban_waiting_confirmation)
        
        confirm_text = get_message(user_lang, "admin_unban_confirm").format(user_id=user_id_to_unban)
        
        await message.answer(
            confirm_text,
            reply_markup=get_confirmation_keyboard(user_lang, "unban_confirm", "unban_cancel")
        )
        
    except ValueError:
        await message.answer(get_message(user_lang, "admin_unban_invalid_id"))

@router.callback_query(F.data == "unban_confirm", IsAdminCallback())
async def admin_unban_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждает разблокировку пользователя"""
    user_lang = get_user_language(callback.from_user.id)
    
    data = await state.get_data()
    user_id_to_unban = data.get('user_id_to_unban')
    
    if not user_id_to_unban:
        await callback.message.edit_text(get_message(user_lang, "admin_error"))
        await state.clear()
        return
    
    banned_users = load_banned_users()
    if user_id_to_unban in banned_users:
        banned_users.remove(user_id_to_unban)
        save_banned_users(banned_users)
    
    await callback.answer()
    await callback.message.edit_text(
        get_message(user_lang, "admin_unban_success").format(user_id=user_id_to_unban),
        reply_markup=get_admin_keyboard(user_lang)
    )
    
    logger.info(f"Админ {callback.from_user.id} разблокировал пользователя {user_id_to_unban}")
    await state.clear()

@router.callback_query(F.data == "unban_cancel", IsAdminCallback())
async def admin_unban_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменяет разблокировку пользователя"""
    user_lang = get_user_language(callback.from_user.id)
    
    await callback.answer()
    await callback.message.edit_text(
        get_message(user_lang, "admin_unban_cancelled"),
        reply_markup=get_admin_keyboard(user_lang)
    )
    await state.clear()

# Список заблокированных пользователей
@router.callback_query(F.data == "admin_banned_list", IsAdminCallback())
async def admin_banned_list(callback: CallbackQuery):
    """Показывает список заблокированных пользователей"""
    user_lang = get_user_language(callback.from_user.id)
    
    banned_users = load_banned_users()
    
    if not banned_users:
        text = get_message(user_lang, "admin_banned_list_empty")
    else:
        user_list = "\n".join([f"• {user_id}" for user_id in banned_users])
        text = get_message(user_lang, "admin_banned_list_text").format(
            count=len(banned_users),
            users=user_list
        )
    
    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_keyboard(user_lang)
    )


# Функция проверки блокировки (для использования в других модулях)
def is_user_banned(user_id: int) -> bool:
    """Проверяет, заблокирован ли пользователь"""
    banned_users = load_banned_users()
    return user_id in banned_users


# Обработчик для не-админов (должен быть в конце)
@router.message(Command("admin", "stats", "broadcast", "ban", "unban"), IsNotAdmin())
async def non_admin_access(message: Message):
    """Обработчик для не-админов, пытающихся использовать админ-команды"""
    user_lang = get_user_language(message.from_user.id)
    logger.warning(f"Попытка доступа к админ-команде от не-админа {message.from_user.id}")
    await message.answer(get_message(user_lang, "admin_access_denied"))
