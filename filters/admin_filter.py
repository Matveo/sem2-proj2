"""
Фильтр для проверки прав администратора
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config.settings import ADMIN_IDS
from utils.logger import logger


class IsAdmin(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором
    """
    
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"
        
        logger.info(f"Проверка админских прав для пользователя {user_id} ({username})")
        logger.info(f"Список админов: {ADMIN_IDS}")
        logger.info(f"Тип user_id: {type(user_id)}, тип админов: {[type(x) for x in ADMIN_IDS]}")
        
        is_admin = user_id in ADMIN_IDS
        
        if is_admin:
            logger.info(f"✅ Админ {user_id} ({username}) подтвержден")
        else:
            logger.warning(f"❌ Пользователь {user_id} ({username}) НЕ является админом")
        
        return is_admin


class IsAdminCallback(BaseFilter):
    """
    Фильтр для проверки прав администратора в callback-запросах
    """
    
    async def __call__(self, callback: CallbackQuery) -> bool:
        user_id = callback.from_user.id
        username = callback.from_user.username or callback.from_user.first_name or "Unknown"
        
        logger.info(f"Проверка админских прав (callback) для пользователя {user_id} ({username})")
        logger.info(f"Список админов: {ADMIN_IDS}")
        
        is_admin = user_id in ADMIN_IDS
        
        if is_admin:
            logger.info(f"✅ Админ {user_id} ({username}) подтвержден (callback)")
        else:
            logger.warning(f"❌ Пользователь {user_id} ({username}) НЕ является админом (callback)")
        
        return is_admin


class IsNotAdmin(BaseFilter):
    """
    Фильтр для проверки, что пользователь НЕ является администратором
    """
    
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        is_not_admin = user_id not in ADMIN_IDS
        
        if is_not_admin:
            logger.info(f"Не-админ {user_id} пытается получить доступ к админ-команде")
        
        return is_not_admin