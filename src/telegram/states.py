from aiogram.fsm.state import State, StatesGroup


class TransactionStates(StatesGroup):
    waiting_confirmation = State()


class SettingsStates(StatesGroup):
    main_menu = State()
    balance_settings = State()
    account_settings = State()
    confirm_balance_mode_change = State()
