"""
Упрощенный антиспам middleware для защиты бота от спама
Проверяет только интервал между сообщениями (минимум 2 секунды)
"""

import time
from typing import Dict, Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from utils.logger import logger


class AntiSpamMiddleware(BaseMiddleware):
    """
    Упрощенный middleware для защиты от спама
    Проверяет только интервал в 2 секунды между сообщениями от одного пользователя
    """
    
    def __init__(self, min_interval: float = 2.0):
        """
        Инициализация middleware
        
        Args:
            min_interval: Минимальный интервал между сообщениями в секундах (по умолчанию 2.0)
        """
        super().__init__()
        self.min_interval = min_interval
        # Словарь для хранения времени последнего сообщения от каждого пользователя
        self.last_message_time: Dict[int, float] = {}
        
        logger.info(f"AntiSpam middleware инициализирован с интервалом {min_interval} секунд")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Основная логика middleware"""
        
        # Получаем пользователя из события
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        
        if not user:
            return await handler(event, data)
        
        user_id = user.id
        current_time = time.time()
        
        # Проверяем, есть ли запись о последнем сообщении пользователя
        if user_id in self.last_message_time:
            time_diff = current_time - self.last_message_time[user_id]
            
            # Если прошло меньше минимального интервала
            if time_diff < self.min_interval:
                remaining_time = self.min_interval - time_diff
                
                logger.info(f"Пользователь {user_id} отправляет сообщения слишком часто. "
                           f"Осталось ждать: {remaining_time:.1f} сек")
                
                # Отправляем предупреждение
                warning_text = (
                    f"⚠️ Пожалуйста, подождите еще {remaining_time:.1f} секунд "
                    f"перед отправкой следующего сообщения."
                )
                
                try:
                    if isinstance(event, Message):
                        await event.answer(warning_text)
                    elif isinstance(event, CallbackQuery):
                        await event.answer(warning_text, show_alert=True)
                except Exception as e:
                    logger.error(f"Ошибка при отправке предупреждения пользователю {user_id}: {e}")
                
                # Блокируем обработку события
                return
        
        # Обновляем время последнего сообщения
        self.last_message_time[user_id] = current_time
        
        # Передаем обработку дальше
        return await handler(event, data)

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы антиспам системы"""
        return {
            "total_users_tracked": len(self.last_message_time),
            "min_interval": self.min_interval
        }

    def reset_user(self, user_id: int) -> bool:
        """
        Сбрасывает ограничения для пользователя (для администраторов)
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если пользователь был сброшен, False если его не было в списке
        """
        if user_id in self.last_message_time:
            del self.last_message_time[user_id]
            logger.info(f"Ограничения для пользователя {user_id} сброшены")
            return True
        return False
