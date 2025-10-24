"""
Configuration Module
Загрузка настроек из .env файла
"""

import os
from pathlib import Path
from typing import Set
from dotenv import load_dotenv

# Загрузка .env из корня проекта
ROOT_DIR = Path(__file__).parent.parent
ENV_PATH = ROOT_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
    print(f"✅ Загружен .env из: {ENV_PATH}")
else:
    print(f"⚠️  Файл .env не найден: {ENV_PATH}")


class Config:
    """Конфигурация приложения"""
    
    # TELEGRAM
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Безопасно получаем ADMIN_USER_ID
    _admin_id = os.getenv("ADMIN_USER_ID", "0")
    try:
        ADMIN_USER_ID: int = int(_admin_id) if _admin_id else 0
    except ValueError:
        ADMIN_USER_ID: int = 0
    
    # DATABASE
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_POOL_MIN_SIZE: int = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
    DB_POOL_MAX_SIZE: int = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
    DB_COMMAND_TIMEOUT: int = int(os.getenv("DB_COMMAND_TIMEOUT", "60"))
    
    # TON
    TON_NETWORK: str = os.getenv("TON_NETWORK", "testnet")
    TON_API_KEY: str = os.getenv("TON_API_KEY", "")
    
    @property
    def TON_API_ENDPOINT(self) -> str:
        if self.TON_NETWORK == "mainnet":
            return "https://toncenter.com/api/v2/"
        return "https://testnet.toncenter.com/api/v2/"
    
    # SECURITY
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    # PATHS
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_FOLDER: Path = BASE_DIR / "uploads"
    LOG_FOLDER: Path = ROOT_DIR / "logs"
    
    # Создание папок
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    LOG_FOLDER.mkdir(exist_ok=True)
    
    # FILE UPLOAD
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: Set[str] = {
        'txt', 'pdf', 'doc', 'docx',
        'png', 'jpg', 'jpeg', 'gif'
    }
    
    # DISPUTE SETTINGS
    MIN_DISPUTE_AMOUNT: float = 10.0
    MAX_DISPUTE_AMOUNT: float = 10000.0
    DEPOSIT_PERCENTAGE: int = 10
    ARBITER_FEE_PERCENTAGE: int = 7
    MIN_ARBITER_DEPOSIT: float = 100.0
    
    # TIME LIMITS (секунды)
    EVIDENCE_UPLOAD_TIME: int = 3 * 24 * 3600
    ARBITER_DECISION_TIME: int = 5 * 24 * 3600
    APPEAL_TIME: int = 24 * 3600
    
    # RATING
    INITIAL_USER_RATING: float = 3.0
    INITIAL_ARBITER_RATING: float = 3.0
    
    # PAGINATION
    DISPUTES_PER_PAGE: int = 5
    ARBITERS_PER_PAGE: int = 5
    
    # LOGGING
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = LOG_FOLDER / "bot.log"
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Проверка конфигурации"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN не установлен")
        
        if not cls.DATABASE_URL:
            errors.append("❌ DATABASE_URL не установлен")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def calculate_deposit(cls, amount: float) -> float:
        """Рассчитать залог"""
        return round(amount * cls.DEPOSIT_PERCENTAGE / 100, 2)
    
    @classmethod
    def calculate_arbiter_fee(cls, amount: float) -> float:
        """Рассчитать комиссию арбитра"""
        return round(amount * cls.ARBITER_FEE_PERCENTAGE / 100, 2)


# Экземпляр конфигурации
config = Config()


if __name__ == "__main__":
    print("=" * 60)
    print("📋 КОНФИГУРАЦИЯ")
    print("=" * 60)
    print(f"BOT_TOKEN:    {'✅' if config.BOT_TOKEN else '❌'}")
    print(f"DATABASE_URL: {'✅' if config.DATABASE_URL else '❌'}")
    print(f"TON_NETWORK:  {config.TON_NETWORK}")
    print(f"MIN_DISPUTE:  ${config.MIN_DISPUTE_AMOUNT}")
    print(f"MAX_DISPUTE:  ${config.MAX_DISPUTE_AMOUNT}")
    print(f"ADMIN_ID:     {config.ADMIN_USER_ID}")
    print("=" * 60)
    
    is_valid, errors = config.validate()
    if not is_valid:
        print("⚠️  ОШИБКИ:")
        for error in errors:
            print(f"  {error}")
    else:
        print("\n✅ Конфигурация валидна!")
