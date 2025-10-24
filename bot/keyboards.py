"""
Keyboards
Клавиатуры и кнопки для Telegram бота
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ========================================
# ГЛАВНЫЕ МЕНЮ
# ========================================

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🆕 Создать спор")
    kb.button(text="📋 Мои споры")
    kb.button(text="⚖️ Стать арбитром")
    kb.button(text="👤 Мой профиль")
    kb.button(text="📊 Статистика")
    kb.button(text="❓ Помощь")
    kb.adjust(2, 2, 2)  # По 2 кнопки в ряду
    return kb.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Отмена")
    return kb.as_markup(resize_keyboard=True)


# ========================================
# КАТЕГОРИИ СПОРОВ
# ========================================

def get_dispute_categories() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с категориями споров"""
    kb = InlineKeyboardBuilder()
    
    kb.button(
        text="🛒 Покупка-продажа товаров",
        callback_data="category:goods_sale"
    )
    kb.button(
        text="💼 Фриланс и услуги",
        callback_data="category:freelance"
    )
    kb.button(
        text="🏠 Аренда",
        callback_data="category:rental"
    )
    kb.button(
        text="🔧 Услуги и работы",
        callback_data="category:services"
    )
    kb.button(
        text="💰 Долг",
        callback_data="category:loan"
    )
    kb.button(
        text="🤝 Совместная покупка",
        callback_data="category:shared_purchase"
    )
    kb.button(
        text="📦 Другое",
        callback_data="category:other"
    )
    
    kb.adjust(1)  # По 1 кнопке в ряду
    return kb.as_markup()


# ========================================
# ДЕЙСТВИЯ СО СПОРОМ
# ========================================

def get_dispute_actions(
    dispute_id: int,
    user_role: str,
    status: str
) -> InlineKeyboardMarkup:
    """
    Действия со спором в зависимости от роли пользователя
    
    Args:
        dispute_id: ID спора
        user_role: 'initiator', 'respondent', 'arbiter'
        status: Статус спора
    """
    kb = InlineKeyboardBuilder()
    
    if user_role == "initiator":
        kb.button(
            text="📎 Добавить доказательства",
            callback_data=f"add_evidence:{dispute_id}"
        )
        if status == "created":
            kb.button(
                text="👥 Пригласить ответчика",
                callback_data=f"invite_respondent:{dispute_id}"
            )
        kb.button(
            text="❌ Отменить спор",
            callback_data=f"cancel_dispute:{dispute_id}"
        )
    
    elif user_role == "respondent":
        kb.button(
            text="📎 Добавить доказательства",
            callback_data=f"add_evidence:{dispute_id}"
        )
        if status == "awaiting_invite":
            kb.button(
                text="✅ Принять участие",
                callback_data=f"accept_dispute:{dispute_id}"
            )
            kb.button(
                text="❌ Отклонить",
                callback_data=f"reject_dispute:{dispute_id}"
            )
    
    elif user_role == "arbiter":
        kb.button(
            text="📋 Просмотреть дело",
            callback_data=f"view_case:{dispute_id}"
        )
        kb.button(
            text="⚖️ Вынести решение",
            callback_data=f"make_decision:{dispute_id}"
        )
    
    kb.button(text="🔙 Назад", callback_data="back_to_disputes")
    kb.adjust(1)
    return kb.as_markup()


# ========================================
# СПЕЦИАЛИЗАЦИИ АРБИТРОВ
# ========================================

def get_arbiter_specializations() -> InlineKeyboardMarkup:
    """Специализации для арбитров"""
    kb = InlineKeyboardBuilder()
    
    kb.button(
        text="📱 Товары и электроника",
        callback_data="spec:goods_electronics"
    )
    kb.button(
        text="💻 Фриланс и IT",
        callback_data="spec:freelance_it"
    )
    kb.button(
        text="🏡 Недвижимость и аренда",
        callback_data="spec:real_estate"
    )
    kb.button(
        text="🎨 Творческие услуги",
        callback_data="spec:creative"
    )
    kb.button(
        text="⚖️ Общие споры",
        callback_data="spec:general"
    )
    
    kb.adjust(1)
    return kb.as_markup()


# ========================================
# ВЫБОР АРБИТРА
# ========================================

def get_arbiter_list(
    arbiters: list,
    dispute_id: int
) -> InlineKeyboardMarkup:
    """
    Список арбитров для выбора
    
    Args:
        arbiters: Список словарей с данными арбитров
        dispute_id: ID спора
    """
    kb = InlineKeyboardBuilder()
    
    for arbiter in arbiters:
        rating_stars = "⭐" * int(arbiter.get('rating', 0))
        full_name = arbiter.get('full_name', 'Арбитр')
        cases = arbiter.get('cases_resolved', 0)
        
        text = f"{full_name} {rating_stars} ({cases} дел)"
        
        kb.button(
            text=text,
            callback_data=f"select_arbiter:{dispute_id}:{arbiter['user_id']}"
        )
    
    kb.button(
        text="🎲 Случайный выбор",
        callback_data=f"random_arbiter:{dispute_id}"
    )
    
    kb.adjust(1)
    return kb.as_markup()


# ========================================
# РЕШЕНИЕ АРБИТРА
# ========================================

def get_decision_keyboard(dispute_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора распределения средств"""
    kb = InlineKeyboardBuilder()
    
    kb.button(
        text="100% истцу",
        callback_data=f"decision:{dispute_id}:100"
    )
    kb.button(
        text="75% истцу / 25% ответчику",
        callback_data=f"decision:{dispute_id}:75"
    )
    kb.button(
        text="50% / 50%",
        callback_data=f"decision:{dispute_id}:50"
    )
    kb.button(
        text="25% истцу / 75% ответчику",
        callback_data=f"decision:{dispute_id}:25"
    )
    kb.button(
        text="100% ответчику",
        callback_data=f"decision:{dispute_id}:0"
    )
    kb.button(
        text="✍️ Своя пропорция",
        callback_data=f"decision:{dispute_id}:custom"
    )
    
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


# ========================================
# ПОДТВЕРЖДЕНИЕ
# ========================================

def get_confirm_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения действия
    
    Args:
        action: Тип действия
        data: Дополнительные данные
    """
    kb = InlineKeyboardBuilder()
    
    kb.button(
        text="✅ Подтвердить",
        callback_data=f"confirm:{action}:{data}"
    )
    kb.button(
        text="❌ Отмена",
        callback_data=f"cancel:{action}:{data}"
    )
    
    kb.adjust(2)
    return kb.as_markup()


# ========================================
# ПАГИНАЦИЯ
# ========================================

def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str
) -> InlineKeyboardMarkup:
    """
    Клавиатура пагинации
    
    Args:
        current_page: Текущая страница (с 1)
        total_pages: Всего страниц
        callback_prefix: Префикс для callback_data
    """
    kb = InlineKeyboardBuilder()
    
    buttons = []
    
    # Кнопка "Назад"
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"{callback_prefix}:page:{current_page - 1}"
            )
        )
    
    # Индикатор страницы
    buttons.append(
        InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="noop"
        )
    )
    
    # Кнопка "Вперёд"
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=f"{callback_prefix}:page:{current_page + 1}"
            )
        )
    
    kb.row(*buttons)
    return kb.as_markup()


# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================

def get_back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
    """Простая кнопка "Назад" """
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data=callback_data)
    return kb.as_markup()


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура помощи с полезными ссылками"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="📖 Как создать спор", callback_data="help:create_dispute")
    kb.button(text="⚖️ Как стать арбитром", callback_data="help:become_arbiter")
    kb.button(text="💰 Тарифы и комиссии", callback_data="help:fees")
    kb.button(text="🔒 Безопасность", callback_data="help:security")
    kb.button(text="❓ FAQ", callback_data="help:faq")
    kb.button(text="📞 Поддержка", callback_data="help:support")
    
    kb.adjust(2)
    return kb.as_markup()
