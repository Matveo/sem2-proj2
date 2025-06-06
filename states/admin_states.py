"""
FSM состояния для администраторской панели
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """
    Состояния для работы админ-панели
    """
    
    # Состояния для рассылки
    broadcast_waiting_message = State()
    broadcast_waiting_confirmation = State()
    
    # Состояния для блокировки пользователей
    ban_waiting_user_id = State()
    ban_waiting_confirmation = State()
    
    # Состояния для разблокировки
    unban_waiting_user_id = State()
    unban_waiting_confirmation = State()
