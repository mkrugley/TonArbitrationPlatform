"""
Main Entry Point
Главный файл запуска Telegram бота
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавь текущую папку в путь
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from bot.handlers import router, set_db
from database.db_manager import DatabaseManager

# ========================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ========================================

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Отключаем слишком verbose логи от библиотек
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)


# ========================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ========================================

db = DatabaseManager(config.DATABASE_URL)


# ========================================
# LIFECYCLE HANDLERS
# ========================================

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК TELEGRAM БОТА")
    logger.info("=" * 60)
    
    # Подключение к базе данных
    try:
        await db.connect()
        logger.info("✅ База данных подключена")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        raise
    
    # Передача экземпляра БД в handlers
    set_db(db)
    logger.info("✅ Менеджер БД передан в обработчики")
    
    # Получение информации о боте
    bot_info = await bot.get_me()
    logger.info(f"✅ Бот запущен: @{bot_info.username}")
    logger.info(f"📋 ID бота: {bot_info.id}")
    logger.info(f"👤 Имя: {bot_info.first_name}")
    
    # Статистика платформы
    try:
        stats = await db.get_platform_stats()
        logger.info("📊 Статистика платформы:")
        logger.info(f"   • Пользователей: {stats['total_users']}")
        logger.info(f"   • Споров: {stats['total_disputes']}")
        logger.info(f"   • Арбитров: {stats['total_arbiters']}")
        logger.info(f"   • Решено: {stats['resolved_disputes']}")
    except Exception as e:
        logger.warning(f"⚠️  Не удалось получить статистику: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ БОТ ГОТОВ К РАБОТЕ!")
    logger.info("=" * 60)


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("=" * 60)
    logger.info("🛑 ОСТАНОВКА БОТА")
    logger.info("=" * 60)
    
    # Отключение от базы данных
    try:
        await db.disconnect()
        logger.info("✅ База данных отключена")
    except Exception as e:
        logger.error(f"❌ Ошибка при отключении БД: {e}")
    
    logger.info("=" * 60)
    logger.info("👋 БОТ ОСТАНОВЛЕН")
    logger.info("=" * 60)


# ========================================
# ГЛАВНАЯ ФУНКЦИЯ
# ========================================

async def main():
    """Главная функция приложения"""
    
    # Проверка конфигурации
    logger.info("🔍 Проверка конфигурации...")
    is_valid, errors = config.validate()
    
    if not is_valid:
        logger.error("❌ ОШИБКИ В КОНФИГУРАЦИИ:")
        for error in errors:
            logger.error(f"   {error}")
        logger.error("❌ Исправьте ошибки в .env файле и перезапустите")
        return
    
    logger.info("✅ Конфигурация валидна")
    
    # Инициализация бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    
    # Инициализация диспетчера
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(router)
    
    # Регистрация startup/shutdown обработчиков
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск polling
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()


# ========================================
# ТОЧКА ВХОДА
# ========================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Получен сигнал прерывания (Ctrl+C)")
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        sys.exit(1)
