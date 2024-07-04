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


@router.message(F.text)
async def unknown_command(message: Message,
                          state: FSMContext):
    await message.answer(localization.get_text('idk', message.from_user.language_code))
    await state.clear()
