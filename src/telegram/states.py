from aiogram.fsm.state import State, StatesGroup


class TransactionStates(StatesGroup):
    waiting_confirmation = State()