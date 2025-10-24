"""
Модели данных для базы данных
Определяют структуру таблиц и типы данных
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


# === ENUMS (Перечисления) ===

class DisputeStatus(Enum):
    """Статусы спора на разных этапах"""
    CREATED = "created"                      # Создан, ожидает приглашения
    AWAITING_INVITE = "awaiting_invite"      # Отправлено приглашение ответчику
    INVITE_ACCEPTED = "invite_accepted"      # Ответчик принял
    AWAITING_DEPOSITS = "awaiting_deposits"  # Ожидание депозитов от обеих сторон
    DEPOSITS_PAID = "deposits_paid"          # Депозиты внесены
    CHOOSING_ARBITER = "choosing_arbiter"    # Выбор арбитра
    ARBITER_CHOSEN = "arbiter_chosen"        # Арбитр выбран
    EVIDENCE_UPLOAD = "evidence_upload"      # Загрузка доказательств
    UNDER_REVIEW = "under_review"            # Арбитр рассматривает дело
    RESOLVED = "resolved"                    # Решение вынесено
    APPEALED = "appealed"                    # Подана апелляция
    APPEAL_REVIEW = "appeal_review"          # Апелляция рассматривается
    APPEAL_RESOLVED = "appeal_resolved"      # Апелляция рассмотрена
    REFUNDED = "refunded"                    # Средства возвращены (отмена)
    CANCELLED = "cancelled"                  # Отменён
    EXPIRED = "expired"                      # Истёк срок


class DisputeCategory(Enum):
    """Категории споров"""
    GOODS_SALE = "goods_sale"                # Купля-продажа товаров
    FREELANCE = "freelance"                  # Фриланс и услуги
    RENTAL = "rental"                        # Аренда
    SERVICES = "services"                    # Услуги и работы
    LOAN = "loan"                            # Долг
    SHARED_PURCHASE = "shared_purchase"      # Совместная покупка
    OTHER = "other"                          # Другое


class ArbiterSpecialization(Enum):
    """Специализации арбитров"""
    GOODS_ELECTRONICS = "goods_electronics"  # Товары и электроника
    FREELANCE_IT = "freelance_it"            # Фриланс и IT
    REAL_ESTATE = "real_estate"              # Недвижимость и аренда
    CREATIVE = "creative"                    # Творческие услуги
    GENERAL = "general"                      # Общие споры


class EvidenceType(Enum):
    """Типы доказательств"""
    TEXT = "text"           # Текстовое описание
    PHOTO = "photo"         # Фотография
    DOCUMENT = "document"   # Документ (PDF, DOC, etc)
    LINK = "link"          # Ссылка


# === DATACLASSES (Модели данных) ===

@dataclass
class User:
    """Модель пользователя"""
    user_id: int                           # Telegram ID
    username: Optional[str]                # Telegram username
    full_name: str                         # Полное имя
    wallet_address: Optional[str] = None   # TON кошелёк
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_arbiter: bool = False               # Является ли арбитром
    disputes_participated: int = 0         # Количество споров
    rating: float = 3.0                    # Рейтинг пользователя (1-5)
    is_blocked: bool = False               # Заблокирован ли


@dataclass
class Dispute:
    """Модель спора"""
    initiator_id: int                      # ID инициатора (истца)
    amount: float                          # Сумма спора (USD)
    description: str                       # Описание спора
    category: DisputeCategory              # Категория
    dispute_id: Optional[int] = None       # ID в базе (автоинкремент)
    respondent_id: Optional[int] = None    # ID ответчика
    respondent_username: Optional[str] = None  # Username ответчика
    status: DisputeStatus = DisputeStatus.CREATED
    arbiter_id: Optional[int] = None       # ID арбитра
    contract_address: Optional[str] = None # Адрес смарт-контракта TON
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    initiator_deposit_paid: bool = False   # Истец внёс депозит
    respondent_deposit_paid: bool = False  # Ответчик внёс депозит
    resolution: Optional[str] = None       # Решение арбитра (текст)
    initiator_share: Optional[int] = None  # Доля истца (0-100%)
    evidence_deadline: Optional[datetime] = None  # Дедлайн доказательств
    decision_deadline: Optional[datetime] = None  # Дедлайн решения


@dataclass
class Arbiter:
    """Модель арбитра"""
    user_id: int                           # Telegram ID
    specialization: ArbiterSpecialization  # Специализация
    deposit_amount: float                  # Размер залога (USD)
    wallet_address: Optional[str] = None   # TON кошелёк
    is_active: bool = True                 # Активен ли
    rating: float = 3.0                    # Рейтинг арбитра (1-5)
    cases_resolved: int = 0                # Рассмотрено дел
    appeals_count: int = 0                 # Количество апелляций
    average_resolution_time: float = 0.0   # Среднее время решения (часы)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    total_earned: float = 0.0              # Всего заработано (USD)


@dataclass
class Evidence:
    """Модель доказательства"""
    dispute_id: int                        # ID спора
    user_id: int                           # ID пользователя (кто загрузил)
    description: str                       # Описание доказательства
    file_type: EvidenceType                # Тип (текст, фото, документ)
    evidence_id: Optional[int] = None      # ID в базе
    file_hash: Optional[str] = None        # SHA256 хэш файла
    file_path: Optional[str] = None        # Путь к файлу
    file_url: Optional[str] = None         # URL (для ссылок)
    uploaded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Decision:
    """Модель решения арбитра"""
    dispute_id: int                        # ID спора
    arbiter_id: int                        # ID арбитра
    initiator_share: int                   # Доля истца (0-100%)
    reasoning: str                         # Обоснование решения
    decision_id: Optional[int] = None      # ID в базе
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_appealed: bool = False              # Подана ли апелляция
    appeal_arbiter_ids: Optional[list[int]] = None  # IDs арбитров апелляции


@dataclass
class Transaction:
    """Модель транзакции в блокчейне"""
    dispute_id: int                        # ID спора
    user_id: int                           # ID пользователя
    tx_hash: str                           # Хэш транзакции TON
    amount: float                          # Сумма (TON)
    tx_type: str                           # deposit, payout, refund
    transaction_id: Optional[int] = None   # ID в базе
    created_at: datetime = field(default_factory=datetime.utcnow)
    confirmed: bool = False                # Подтверждена ли


@dataclass
class Review:
    """Модель отзыва об арбитре"""
    arbiter_id: int                        # ID арбитра
    reviewer_id: int                       # ID пользователя (кто оставил)
    dispute_id: int                        # ID спора
    rating: int                            # Оценка (1-5)
    comment: Optional[str] = None          # Комментарий
    review_id: Optional[int] = None        # ID в базе
    created_at: datetime = field(default_factory=datetime.utcnow)


# === HELPER FUNCTIONS ===

def status_emoji(status: DisputeStatus) -> str:
    """Возвращает emoji для статуса спора"""
    emoji_map = {
        DisputeStatus.CREATED: "🆕",
        DisputeStatus.AWAITING_INVITE: "📨",
        DisputeStatus.INVITE_ACCEPTED: "✅",
        DisputeStatus.AWAITING_DEPOSITS: "💳",
        DisputeStatus.DEPOSITS_PAID: "💰",
        DisputeStatus.CHOOSING_ARBITER: "👥",
        DisputeStatus.ARBITER_CHOSEN: "⚖️",
        DisputeStatus.EVIDENCE_UPLOAD: "📎",
        DisputeStatus.UNDER_REVIEW: "🔍",
        DisputeStatus.RESOLVED: "✅",
        DisputeStatus.APPEALED: "🔄",
        DisputeStatus.APPEAL_REVIEW: "⚖️",
        DisputeStatus.APPEAL_RESOLVED: "✅",
        DisputeStatus.REFUNDED: "💸",
        DisputeStatus.CANCELLED: "❌",
        DisputeStatus.EXPIRED: "⏰"
    }
    return emoji_map.get(status, "📝")


def status_text_ru(status: DisputeStatus) -> str:
    """Возвращает текст статуса на русском"""
    text_map = {
        DisputeStatus.CREATED: "Создан",
        DisputeStatus.AWAITING_INVITE: "Ожидание приглашения",
        DisputeStatus.INVITE_ACCEPTED: "Приглашение принято",
        DisputeStatus.AWAITING_DEPOSITS: "Ожидание депозитов",
        DisputeStatus.DEPOSITS_PAID: "Депозиты внесены",
        DisputeStatus.CHOOSING_ARBITER: "Выбор арбитра",
        DisputeStatus.ARBITER_CHOSEN: "Арбитр выбран",
        DisputeStatus.EVIDENCE_UPLOAD: "Загрузка доказательств",
        DisputeStatus.UNDER_REVIEW: "На рассмотрении",
        DisputeStatus.RESOLVED: "Решён",
        DisputeStatus.APPEALED: "Подана апелляция",
        DisputeStatus.APPEAL_REVIEW: "Апелляция рассматривается",
        DisputeStatus.APPEAL_RESOLVED: "Апелляция рассмотрена",
        DisputeStatus.REFUNDED: "Возврат средств",
        DisputeStatus.CANCELLED: "Отменён",
        DisputeStatus.EXPIRED: "Истёк срок"
    }
    return text_map.get(status, "Неизвестно")


def category_text_ru(category: DisputeCategory) -> str:
    """Возвращает текст категории на русском"""
    text_map = {
        DisputeCategory.GOODS_SALE: "Купля-продажа товаров",
        DisputeCategory.FREELANCE: "Фриланс и услуги",
        DisputeCategory.RENTAL: "Аренда",
        DisputeCategory.SERVICES: "Услуги и работы",
        DisputeCategory.LOAN: "Долг",
        DisputeCategory.SHARED_PURCHASE: "Совместная покупка",
        DisputeCategory.OTHER: "Другое"
    }
    return text_map.get(category, "Неизвестно")


def specialization_text_ru(spec: ArbiterSpecialization) -> str:
    """Возвращает текст специализации на русском"""
    text_map = {
        ArbiterSpecialization.GOODS_ELECTRONICS: "Товары и электроника",
        ArbiterSpecialization.FREELANCE_IT: "Фриланс и IT",
        ArbiterSpecialization.REAL_ESTATE: "Недвижимость и аренда",
        ArbiterSpecialization.CREATIVE: "Творческие услуги",
        ArbiterSpecialization.GENERAL: "Общие споры"
    }
    return text_map.get(spec, "Неизвестно")
