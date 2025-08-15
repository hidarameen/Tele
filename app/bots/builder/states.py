from aiogram.fsm.state import StatesGroup, State

class AddBotState(StatesGroup):
	waiting_details = State()

class SettingsState(StatesGroup):
	waiting_timezone = State()

class UserbotState(StatesGroup):
	waiting_session_string = State()
	waiting_phone = State()
	waiting_code = State()
	waiting_2fa = State()

class TaskState(StatesGroup):
	waiting_new_task_name = State()
	waiting_rename = State()
	waiting_switch_type = State()
	waiting_select_session = State()