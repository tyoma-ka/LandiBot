from aiogram import Router, F
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.state import StatesGroup, State
from config_db import get_database_connection
from config_reader import config
from filters.user_filter import UserFilter
from keyboards import kb_user
from localization import localization
from aiogram.fsm.context import FSMContext

router = Router()
router.message.filter(
    UserFilter(user_type="NonUser")
)

db = get_database_connection()


class RegisterStudent(StatesGroup):
    registration = State()


@router.message(StateFilter(None), Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(localization.get_text('hey_nonuser', message.from_user.language_code), parse_mode="HTML")
    await state.set_state(RegisterStudent.registration)


@router.message(Command("teacher"))
async def cmd_admin(
        message: Message,
        command: CommandObject,
        state: FSMContext):
    await state.clear()
    if command.args is None:
        await message.answer(f"{localization.get_text('error', message.from_user.language_code)}{localization.get_text('no_password_error', message.from_user.language_code)}")
        return
    password = command.args
    if password != config.admin_password.get_secret_value():
        await message.answer(localization.get_text('wrong_password', message.from_user.language_code))
        return
    db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username, True)
    await message.answer(f"{localization.get_text('successful_registration', message.from_user.language_code)}\n{localization.get_text('hey_teacher', message.from_user.language_code)}",
                         reply_markup=kb_user.make_teacher_keyboard(message.from_user.language_code))


@router.message(RegisterStudent.registration)
async def cmd_register(message: Message, state: FSMContext):
    words = message.text.split()

    # Check if there are exactly 3 words
    if len(words) != 3:
        await message.answer(localization.get_text('wrong_name_format', message.from_user.language_code))
        return
    if words[-1] != config.special_code.get_secret_value():
        await message.answer(localization.get_text('wrong_special_code', message.from_user.language_code))
        return
    db.add_user(message.from_user.id, words[0], words[1], message.from_user.username)
    await message.answer(localization.get_text('successfully_registered', message.from_user.language_code), reply_markup=kb_user.make_start_keyboard(message.from_user.language_code))
    await state.clear()

