"""
Handlers
Обработчики команд и сообщений Telegram бота
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
import logging
import random

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from database.models import (
    User, Dispute, Arbiter, Evidence,
    DisputeCategory, DisputeStatus, ArbiterSpecialization, EvidenceType,
    category_text_ru, status_emoji
)
from config import config
from bot.keyboards import (
    get_main_menu,
    get_cancel_keyboard,
    get_dispute_categories,
    get_arbiter_specializations,
    get_dispute_actions,
    get_arbiter_list,
    get_decision_keyboard,
    get_confirm_keyboard,
    get_help_keyboard,
    get_back_button
)
from bot.states import (
    CreateDisputeStates,
    BecomeArbiterStates,
    AddEvidenceStates,
    MakeDecisionStates
)

# Инициализация
router = Router()
logger = logging.getLogger(__name__)

# База данных (будет инициализирована в main.py)
db: DatabaseManager = None


def set_db(database_manager: DatabaseManager):
    """Установка экземпляра менеджера БД"""
    global db
    db = database_manager

# Инициализация
router = Router()
logger = logging.getLogger(__name__)

# База данных (будет инициализирована в main.py)
db: DatabaseManager = None


def set_db(database_manager: DatabaseManager):
    """Установка экземпляра менеджера БД"""
    global db
    db = database_manager


# ========================================
# ОСНОВНЫЕ КОМАНДЫ
# ========================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    # Регистрация/обновление пользователя
    user = User(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    await db.create_user(user)
    await db.update_user_activity(user.user_id)
    
    welcome_text = (
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        "Добро пожаловать в <b>Децентрализованную Арбитражную Платформу</b> на TON.\n\n"
        "🔹 Быстрое разрешение споров за 3-7 дней\n"
        "🔹 Прозрачность через блокчейн\n"
        "🔹 Автоматическое исполнение решений\n\n"
        "Выберите действие из меню ниже:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    """Помощь и инструкции"""
    help_text = (
        "📖 <b>Как пользоваться платформой</b>\n\n"
        "<b>Для создания спора:</b>\n"
        "1. Нажмите '🆕 Создать спор'\n"
        "2. Опишите ситуацию подробно\n"
        "3. Укажите сумму спора ($10-$10,000)\n"
        "4. Выберите категорию\n"
        "5. Пригласите вторую сторону\n\n"
        "<b>Процесс разрешения:</b>\n"
        "• Обе стороны вносят депозиты (10%)\n"
        "• Загружают доказательства (3 дня)\n"
        "• Выбирают арбитра\n"
        "• Арбитр выносит решение (5 дней)\n"
        "• Средства распределяются автоматически\n\n"
        f"<b>Параметры:</b>\n"
        f"• Минимум: ${config.MIN_DISPUTE_AMOUNT}\n"
        f"• Максимум: ${config.MAX_DISPUTE_AMOUNT}\n"
        f"• Залог: {config.DEPOSIT_PERCENTAGE}%\n"
        f"• Комиссия: {config.ARBITER_FEE_PERCENTAGE}%\n\n"
        "Выберите раздел для подробной информации:"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_help_keyboard(),
        parse_mode="HTML"
    )


# ========================================
# СОЗДАНИЕ СПОРА
# ========================================

@router.message(F.text == "🆕 Создать спор")
async def start_create_dispute(message: Message, state: FSMContext):
    """Начало создания спора"""
    await state.set_state(CreateDisputeStates.waiting_for_description)
    
    await message.answer(
        "📝 <b>Шаг 1/4: Описание спора</b>\n\n"
        "Опишите ситуацию максимально подробно:\n"
        "• Суть конфликта\n"
        "• Что произошло\n"
        "• Ваши требования\n\n"
        "💡 Минимум 50 символов\n\n"
        "Чем подробнее опишете, тем легче арбитру принять решение.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(CreateDisputeStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания спора"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Создание спора отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    if len(message.text) < 50:
        await message.answer(
            "❗ Описание слишком короткое. Напишите минимум 50 символов."
        )
        return
    
    await state.update_data(description=message.text)
    await state.set_state(CreateDisputeStates.waiting_for_amount)
    
    await message.answer(
        "💰 <b>Шаг 2/4: Сумма спора</b>\n\n"
        f"Укажите сумму в USD (от ${config.MIN_DISPUTE_AMOUNT} до ${config.MAX_DISPUTE_AMOUNT}):\n\n"
        "Например: <code>150</code>",
        parse_mode="HTML"
    )


@router.message(CreateDisputeStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    """Обработка суммы спора"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Создание спора отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    try:
        amount = float(message.text.replace(",", ".").replace("$", ""))
        
        is_valid, error_msg = config.validate_amount(amount)
        if not is_valid:
            await message.answer(f"❗ {error_msg}")
            return
        
        await state.update_data(amount=amount)
        await state.set_state(CreateDisputeStates.waiting_for_category)
        
        deposit = config.calculate_deposit(amount)
        fee = config.calculate_arbiter_fee(amount)
        
        await message.answer(
            "📂 <b>Шаг 3/4: Категория спора</b>\n\n"
            f"💰 Сумма спора: <b>${amount:.2f}</b>\n"
            f"💳 Ваш залог: <b>${deposit:.2f}</b> ({config.DEPOSIT_PERCENTAGE}%)\n"
            f"⚖️ Комиссия арбитру: <b>${fee:.2f}</b> ({config.ARBITER_FEE_PERCENTAGE}%)\n\n"
            "Выберите категорию спора:",
            reply_markup=get_dispute_categories(),
            parse_mode="HTML"
        )
        
    except ValueError:
        await message.answer(
            "❗ Неверный формат. Введите число, например: <code>150</code>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("category:"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category_value = callback.data.split(":")[1]
    category = DisputeCategory(category_value)
    
    await state.update_data(category=category)
    await state.set_state(CreateDisputeStates.waiting_for_respondent)
    
    await callback.message.edit_text(
        f"✅ Категория: <b>{category_text_ru(category)}</b>",
        parse_mode="HTML"
    )
    
    await callback.message.answer(
        "👤 <b>Шаг 4/4: Вторая сторона</b>\n\n"
        "Укажите username второго участника в Telegram:\n\n"
        "Например: <code>@username</code>\n\n"
        "⚠️ Убедитесь что человек согласен участвовать!",
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.message(CreateDisputeStates.waiting_for_respondent)
async def process_respondent(message: Message, state: FSMContext):
    """Обработка username ответчика"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Создание спора отменено.",
            reply_markup=get_main_menu()
        )
        return
    
    username = message.text.strip()
    if not username.startswith("@") or len(username) < 5:
        await message.answer(
            "❗ Неверный формат. Должно быть: <code>@username</code>",
            parse_mode="HTML"
        )
        return
    
    # Получаем все данные
    data = await state.get_data()
    
    # Создаём спор в БД
    dispute = Dispute(
        initiator_id=message.from_user.id,
        amount=data['amount'],
        description=data['description'],
        category=data['category'],
        respondent_username=username
    )
    
    dispute_id = await db.create_dispute(dispute)
    
    await state.clear()
    
    deposit = config.calculate_deposit(data['amount'])
    
    success_text = (
        "✅ <b>Спор создан успешно!</b>\n\n"
        f"🆔 Номер дела: <code>#{dispute_id}</code>\n"
        f"💰 Сумма: ${data['amount']:.2f}\n"
        f"💳 Ваш залог: ${deposit:.2f}\n"
        f"👤 Ответчик: {username}\n\n"
        "📨 Отправьте ответчику эту ссылку:\n"
        f"<code>https://t.me/{(await message.bot.get_me()).username}?start=dispute_{dispute_id}</code>\n\n"
        "⏳ <b>Статус:</b> Ожидание принятия\n\n"
        "После принятия обе стороны должны внести депозиты."
    )
    
    await message.answer(
        success_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    
    logger.info(f"✅ Создан спор #{dispute_id} пользователем {message.from_user.id}")


# ========================================
# МОИ СПОРЫ
# ========================================

@router.message(F.text == "📋 Мои споры")
async def show_my_disputes(message: Message):
    """Показать споры пользователя"""
    user_id = message.from_user.id
    
    # Обновляем активность
    await db.update_user_activity(user_id)
    
    # Получаем споры
    disputes_initiator = await db.get_user_disputes(user_id, as_initiator=True, limit=5)
    disputes_respondent = await db.get_user_disputes(user_id, as_initiator=False, limit=5)
    
    if not disputes_initiator and not disputes_respondent:
        await message.answer(
            "📋 У вас пока нет споров.\n\n"
            "Нажмите '🆕 Создать спор' чтобы начать.",
            reply_markup=get_main_menu()
        )
        return
    
    text = "📋 <b>Ваши споры:</b>\n\n"
    
    if disputes_initiator:
        text += "<b>Вы — истец:</b>\n"
        for dispute in disputes_initiator[:3]:
            emoji = status_emoji(DisputeStatus(dispute['status']))
            text += (
                f"\n{emoji} Дело <code>#{dispute['dispute_id']}</code>\n"
                f"💰 ${dispute['amount']:.2f}\n"
                f"📅 {dispute['created_at'].strftime('%d.%m.%Y')}\n"
            )
    
    if disputes_respondent:
        text += "\n<b>Вы — ответчик:</b>\n"
        for dispute in disputes_respondent[:3]:
            emoji = status_emoji(DisputeStatus(dispute['status']))
            text += (
                f"\n{emoji} Дело <code>#{dispute['dispute_id']}</code>\n"
                f"💰 ${dispute['amount']:.2f}\n"
                f"📅 {dispute['created_at'].strftime('%d.%m.%Y')}\n"
            )
    
    text += "\n💡 Для подробностей введите: <code>/dispute ID</code>"
    
    await message.answer(text, parse_mode="HTML")


# ========================================
# ПРОФИЛЬ
# ========================================

@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    user = await db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("❗ Ошибка загрузки профиля")
        return
    
    profile_text = (
        f"👤 <b>Профиль: {user['full_name']}</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"📅 Регистрация: {user['created_at'].strftime('%d.%m.%Y')}\n"
        f"⚖️ Участие в спорах: {user['disputes_participated']}\n"
        f"⭐ Рейтинг: {user['rating']:.1f}/5.0\n"
    )
    
    if user['is_arbiter']:
        arbiter = await db.get_arbiter(user['user_id'])
        if arbiter:
            profile_text += (
                f"\n<b>📊 Статус арбитра:</b>\n"
                f"Рассмотрено дел: {arbiter['cases_resolved']}\n"
                f"Рейтинг: {arbiter['rating']:.1f}/5.0\n"
                f"Заработано: ${arbiter['total_earned']:.2f}\n"
            )
    
    if user['wallet_address']:
        wallet_short = f"{user['wallet_address'][:8]}...{user['wallet_address'][-6:]}"
        profile_text += f"\n💼 Кошелёк: <code>{wallet_short}</code>"
    else:
        profile_text += "\n💼 Кошелёк: <i>не подключен</i>"
    
    await message.answer(profile_text, parse_mode="HTML")


# ========================================
# СТАТЬ АРБИТРОМ
# ========================================

@router.message(F.text == "⚖️ Стать арбитром")
async def start_become_arbiter(message: Message, state: FSMContext):
    """Начало регистрации арбитром"""
    user = await db.get_user(message.from_user.id)
    
    if user and user['is_arbiter']:
        await message.answer(
            "✅ Вы уже зарегистрированы как арбитр!",
            reply_markup=get_main_menu()
        )
        return
    
    await state.set_state(BecomeArbiterStates.waiting_for_specialization)
    
    await message.answer(
        "⚖️ <b>Регистрация арбитра</b>\n\n"
        f"Для регистрации потребуется залог: <b>${config.MIN_ARBITER_DEPOSIT}</b>\n\n"
        "<b>Преимущества:</b>\n"
        f"• Доход {config.ARBITER_FEE_PERCENTAGE}% от каждого спора\n"
        "• Гибкий график работы\n"
        "• Помощь людям в решении конфликтов\n\n"
        "Выберите вашу специализацию:",
        reply_markup=get_arbiter_specializations(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("spec:"))
async def process_specialization(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора специализации"""
    spec_value = callback.data.split(":")[1]
    
    spec_names = {
        "goods_electronics": "Товары и электроника",
        "freelance_it": "Фриланс и IT",
        "real_estate": "Недвижимость и аренда",
        "creative": "Творческие услуги",
        "general": "Общие споры"
    }
    
    await state.update_data(specialization=spec_value)
    
    await callback.message.edit_text(
        f"✅ Специализация: <b>{spec_names[spec_value]}</b>",
        parse_mode="HTML"
    )
    
    await callback.message.answer(
        "💼 <b>Подключение TON кошелька</b>\n\n"
        f"Для внесения залога (${config.MIN_ARBITER_DEPOSIT}) необходимо подключить TON кошелёк.\n\n"
        "⚠️ <i>Функция TON Connect в разработке</i>\n\n"
        "Пока что регистрация арбитров временно недоступна.\n"
        "Следите за обновлениями!",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()


# ========================================
# СТАТИСТИКА
# ========================================

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    """Показать статистику платформы"""
    stats = await db.get_platform_stats()
    
    stats_text = (
        "📊 <b>Статистика платформы</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"📋 Всего споров: <b>{stats['total_disputes']}</b>\n"
        f"⚖️ Активных арбитров: <b>{stats['total_arbiters']}</b>\n"
        f"✅ Решённых споров: <b>{stats['resolved_disputes']}</b>\n"
        f"💰 Общая сумма споров: <b>${stats['total_amount']:.2f}</b>\n"
    )
    
    await message.answer(stats_text, parse_mode="HTML")


# ========================================
# ОБРАБОТКА CALLBACK ЗАПРОСОВ
# ========================================

@router.callback_query(F.data.startswith("help:"))
async def process_help_callback(callback: CallbackQuery):
    """Обработка запросов помощи"""
    topic = callback.data.split(":")[1]
    
    help_texts = {
        "create_dispute": (
            "📖 <b>Как создать спор</b>\n\n"
            "1. Нажмите '🆕 Создать спор'\n"
            "2. Подробно опишите ситуацию (минимум 50 символов)\n"
            "3. Укажите сумму спора в USD\n"
            "4. Выберите подходящую категорию\n"
            "5. Укажите @username второго участника\n\n"
            "После создания отправьте ответчику ссылку на спор."
        ),
        "become_arbiter": (
            "⚖️ <b>Как стать арбитром</b>\n\n"
            f"1. Внесите залог ${config.MIN_ARBITER_DEPOSIT}\n"
            "2. Выберите специализацию\n"
            "3. Получайте уведомления о новых делах\n"
            f"4. Зарабатывайте {config.ARBITER_FEE_PERCENTAGE}% с каждого спора\n\n"
            "Требования:\n"
            "• Объективность и честность\n"
            "• Готовность разбираться в деталях\n"
            "• Время на рассмотрение дел"
        ),
        "fees": (
            "💰 <b>Тарифы и комиссии</b>\n\n"
            f"Залог участников: {config.DEPOSIT_PERCENTAGE}% от суммы\n"
            f"Комиссия арбитру: {config.ARBITER_FEE_PERCENTAGE}% от суммы\n"
            f"Минимальная сумма: ${config.MIN_DISPUTE_AMOUNT}\n"
            f"Максимальная сумма: ${config.MAX_DISPUTE_AMOUNT}\n\n"
            "Комиссия TON сети: ~$0.01-0.05"
        ),
        "security": (
            "🔒 <b>Безопасность</b>\n\n"
            "• Средства блокируются в смарт-контрактах TON\n"
            "• Решения записываются в блокчейн\n"
            "• Доказательства хешируются (SHA256)\n"
            "• Приватные ключи не хранятся\n"
            "• Все операции прозрачны и проверяемы"
        ),
        "faq": (
            "❓ <b>FAQ</b>\n\n"
            "<b>В:</b> Сколько времени занимает решение?\n"
            "<b>О:</b> В среднем 3-5 дней\n\n"
            "<b>В:</b> Можно ли отменить спор?\n"
            "<b>О:</b> Да, до внесения депозитов\n\n"
            "<b>В:</b> Что если не согласен с решением?\n"
            "<b>О:</b> Можно подать апелляцию в течение 24 часов"
        ),
        "support": (
            "📞 <b>Поддержка</b>\n\n"
            "По всем вопросам обращайтесь:\n"
            "• Email: support@example.com\n"
            "• Telegram: @support_bot\n\n"
            "Мы отвечаем в течение 24 часов."
        )
    }
    
    text = help_texts.get(topic, "Информация временно недоступна")
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_button("help"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def back_to_help(callback: CallbackQuery):
    """Вернуться к меню помощи"""
    await cmd_help(callback.message)
    await callback.answer()


@router.callback_query(F.data == "back_to_disputes")
async def back_to_disputes(callback: CallbackQuery):
    """Вернуться к списку споров"""
    await show_my_disputes(callback.message)
    await callback.answer()


# ========================================
# ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД
# ========================================

@router.message()
async def unknown_message(message: Message):
    """Обработка неизвестных сообщений"""
    await message.answer(
        "❓ Не понимаю команду.\n\n"
        "Используйте меню или команду /help",
        reply_markup=get_main_menu()
    )
