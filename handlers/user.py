from aiogram import Router, F
from aiogram.filters import BaseFilter
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from config_db import get_database_connection
from handlers import teacher, student
from filters.user_filter import UserFilter
from filters.text_filter import TextFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from localization import localization
from keyboards import kb_user

router = Router()
router.message.filter(
    UserFilter(user_type="User")
)

db = get_database_connection()
router.include_routers(teacher.router, student.router)


class DeleteAccount(StatesGroup):
    deleting_account = State()


@router.message(StateFilter(None), Command("delete_account"))
async def ask_for_delete(message: Message, state: FSMContext):
    await message.answer(localization.get_text('asking_for_deleting', message.from_user.language_code),
                         reply_markup=kb_user.make_yes_no_keyboard(message.from_user.language_code))
    await state.set_state(DeleteAccount.deleting_account)


@router.message(DeleteAccount.deleting_account, TextFilter('yes'))
async def delete_account(message: Message, state: FSMContext):
    db.delete_user_by_id(message.from_user.id)
    await state.clear()
    await message.answer(localization.get_text('deleting_approval', message.from_user.language_code),
                         reply_markup=ReplyKeyboardRemove())


@router.callback_query(DeleteAccount.deleting_account, F.data == 'yes')
async def delete_account2(callback: CallbackQuery, state: FSMContext):
    db.delete_user_by_id(callback.from_user.id)
    await state.clear()
    await callback.message.answer(localization.get_text('deleting_approval', callback.from_user.language_code),
                                  reply_markup=ReplyKeyboardRemove())
    await callback.answer()


@router.callback_query(DeleteAccount.deleting_account, F.data == 'no')
async def cancel2(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(localization.get_text('deleting_cancel', callback.from_user.language_code))
    await callback.answer()


@router.message(DeleteAccount.deleting_account)
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(localization.get_text('deleting_cancel', message.from_user.language_code))
