"""
Middleware для проверки и установки языка пользователя
"""

from typing import Dict, Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.formatters import get_user_language, set_user_language, USER_SETTINGS


class CheckLanguageMiddleware(BaseMiddleware):
    """
    Middleware для автоматической проверки и установки языка пользователя
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Проверяет язык пользователя и устанавливает его при необходимости"""
        
        # Получаем пользователя из события
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        if user:
            user_id = user.id
            
            # Проверяем, есть ли сохраненный язык пользователя
            user_lang = get_user_language(user_id)
            
            # Если язык не установлен (возвращается дефолтный "en"), 
            # проверяем, есть ли реально сохраненная запись пользователя
            if user_lang == "en" and user_id not in USER_SETTINGS:
                telegram_lang = user.language_code or 'en'
                
                # Устанавливаем язык на основе языка Telegram или английский по умолчанию
                if telegram_lang.startswith('ru'):
                    default_lang = 'ru'
                else:
                    default_lang = 'en'
                
                set_user_language(user_id, default_lang)
                user_lang = default_lang
            
            # Добавляем язык пользователя в данные для обработчиков
            data['user_language'] = user_lang
        
        return await handler(event, data)