"""
FSM States
Состояния конечного автомата для диалогов бота
"""

from aiogram.fsm.state import State, StatesGroup


class CreateDisputeStates(StatesGroup):
    """Состояния для создания спора"""
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_respondent = State()
    confirming = State()


class BecomeArbiterStates(StatesGroup):
    """Состояния для регистрации арбитра"""
    waiting_for_specialization = State()
    waiting_for_deposit = State()
    waiting_for_wallet = State()
    confirming = State()


class AddEvidenceStates(StatesGroup):
    """Состояния для добавления доказательств"""
    waiting_for_dispute_id = State()
    waiting_for_description = State()
    waiting_for_file = State()


class MakeDecisionStates(StatesGroup):
    """Состояния для вынесения решения арбитром"""
    waiting_for_dispute_id = State()
    waiting_for_share = State()
    waiting_for_reasoning = State()
    confirming = State()


class AppealStates(StatesGroup):
    """Состояния для подачи апелляции"""
    waiting_for_dispute_id = State()
    waiting_for_reason = State()
    confirming = State()
