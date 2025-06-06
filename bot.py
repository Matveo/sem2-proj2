import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from config.settings import BOT_TOKEN
from routers.commands import router as commands_router
from routers.handlers.translation import router as translation_router
from routers.handlers.settings import router as settings_router
from routers.handlers.admin import router as admin_router
from middlewares.check_language import CheckLanguageMiddleware
from middlewares.antispam import AntiSpamMiddleware
from utils.logger import logger
from utils.formatters import load_user_settings  # Ensure user settings are loaded
from config.settings import ADMIN_IDS

async def set_bot_commands(bot: Bot):
    """
    Устанавливает команды бота для меню
    """
    # Основные команды для всех пользователей
    user_commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Показать справку"),
        BotCommand(command="translate", description="🔄 Перевести текст"),
        BotCommand(command="setlanguage", description="🌐 Изменить язык интерфейса"),
        BotCommand(command="history", description="📜 История переводов"),
        BotCommand(command="clear_history", description="🗑️ Очистить историю"),
    ]
    
    # Команды для админов
    admin_commands = user_commands + [
        BotCommand(command="admin", description="⚙️ Админ-панель"),
        BotCommand(command="stats", description="📊 Статистика бота"),
        BotCommand(command="broadcast", description="📢 Рассылка сообщений"),
        BotCommand(command="ban", description="🚫 Заблокировать пользователя"),
        BotCommand(command="unban", description="✅ Разблокировать пользователя"),
    ]
    
    try:
        # Устанавливаем команды для всех пользователей по умолчанию
        await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
        logger.info(f"Установлены команды для всех пользователей: {len(user_commands)} команд")
        
        # Устанавливаем расширенные команды для каждого админа
        for admin_id in ADMIN_IDS:
            await bot.set_my_commands(
                admin_commands, 
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
            logger.info(f"Установлены админ-команды для пользователя {admin_id}: {len(admin_commands)} команд")
            
    except Exception as e:
        logger.error(f"Ошибка при установке команд бота: {e}")

async def main():
    """
    Главная функция запуска бота
    """
    # Проверяем наличие токена
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в переменных окружения")
        sys.exit("BOT_TOKEN не найден в переменных окружения")
    
    # Создаем хранилище состояний
    storage = MemoryStorage()
      # Создаем бота и диспетчер
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=storage)      # Регистрируем middleware (порядок важен!)
    # 1. Проверяем язык пользователя
    dp.message.middleware(CheckLanguageMiddleware())
    dp.callback_query.middleware(CheckLanguageMiddleware())
    
    # 2. Антиспам защита
    dp.message.middleware(AntiSpamMiddleware())
    dp.callback_query.middleware(AntiSpamMiddleware())
      # Регистрируем роутеры
    dp.include_router(admin_router)
    dp.include_router(translation_router)
    dp.include_router(settings_router)
    dp.include_router(commands_router)
    logger.info("Бот запускается...")
    
    # Загружаем пользовательские настройки
    load_user_settings()
    
    # Устанавливаем команды бота
    await set_bot_commands(bot)
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)