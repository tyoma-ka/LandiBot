from aiogram import Router, F
from aiogram.filters import BaseFilter
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config_db import get_database_connection
from config_reader import config
from filters.user_filter import UserFilter
from filters.text_filter import TextFilter
from localization import localization
from aiogram.fsm.context import FSMContext
from formating import lessonformat, timeformat
from keyboards import kb_user
from datetime import datetime
import calendar


class JoinLesson(StatesGroup):
    joining_lesson = State()
    are_you_sure = State()


router = Router()
router.message.filter(
    UserFilter(user_type="Student")
)

db = get_database_connection()


@router.message(StateFilter(None), Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        localization.get_text('hey_student', message.from_user.language_code),
        reply_markup=kb_user.make_start_keyboard(message.from_user.language_code)
    )


@router.message(TextFilter('info'))
@router.message(StateFilter(None), Command("info"))
async def cmd_info(message: Message):
    await message.answer(localization.get_text('student_info', message.from_user.language_code))


@router.message(StateFilter(None), Command("teacher"))
async def cmd_admin(
        message: Message,
        command: CommandObject):
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


@router.message(TextFilter('timetable'))
@router.message(StateFilter(None), Command("timetable"))
async def cmd_view_timetable(message: Message):
    data = lessonformat.format_schedule_by_day(db.get_timetable_by_week(), message.from_user.language_code)
    await message.answer(
        f"{localization.get_text('current_timetable', message.from_user.language_code)}\n{localization.get_text('ask_register_lesson', message.from_user.language_code)}\n{data}")


@router.callback_query(F.data == "timetable")
async def timetable_callback(callback: CallbackQuery):
    data = lessonformat.format_schedule_by_day(db.get_timetable_by_week(), callback.from_user.language_code)
    await callback.message.answer(
        f"{localization.get_text('current_timetable', callback.from_user.language_code)}\n{localization.get_text('ask_register_lesson', callback.from_user.language_code)}\n{data}")
    await callback.answer()


@router.message(StateFilter(None), Command("join"))
async def cmd_join_lesson(
        message: Message,
        command: CommandObject):
    if command.args is None:
        await message.answer(f"{localization.get_text('error', message.from_user.language_code)}{localization.get_text('no_lesson_id', message.from_user.language_code)}")
        return
    lesson_id = command.args
    if not lesson_id.isdigit():
        await message.answer(localization.get_text('wrong_lesson_id', message.from_user.language_code))
        return

    lesson = db.get_lesson_by_id(lesson_id)
    if not lesson:
        await message.answer(f"{localization.get_text('wrong_lesson_id', message.from_user.language_code)}")
        return
    lesson = lesson[0]
    lesson_id, date_time_str, lesson_name, available_spots = lesson
    if not timeformat.check_time_is_future(date_time_str):
        await message.answer(f"{localization.get_text('lesson_is_in_past', message.from_user.language_code)}")
        return
    number_of_registrations = db.count_registrations_for_lesson(lesson_id)
    max_number = available_spots
    if db.check_student_registration_by_id(message.from_user.id, lesson_id):
        await message.answer(localization.get_text('already_registered_for_lesson', message.from_user.language_code))
        return
    if max_number - number_of_registrations <= 0:
        await message.answer(f"{localization.get_text('no_places_left', message.from_user.language_code)}")
        return
    res = db.register_student_for_lesson(message.from_user.id, lesson_id)
    if res != 'ok':
        await message.answer(f"{localization.get_text('error', message.from_user.language_code)}{res}")
        return
    await message.answer(
        f"{localization.get_text('successful_registration_for_lesson', message.from_user.language_code)}:\n📆 {localization.get_text(timeformat.get_weekday(lesson[1]).lower(), message.from_user.language_code)}\n{lessonformat.formate_lesson(lesson, message.from_user.language_code)}")


@router.callback_query(F.data == "my_lessons")
async def my_lessons_callback(callback: CallbackQuery):
    lessons_of_student = db.get_lessons_of_student(callback.from_user.id)
    formated_schedule = lessonformat.format_schedule_by_day(lessons_of_student, callback.from_user.language_code, False)
    if formated_schedule == '\n':
        answer_string = f"{localization.get_text('no_lessons_to_show', callback.from_user.language_code)}"
    else:
        answer_string = f"{localization.get_text('your_lessons', callback.from_user.language_code)}\n{formated_schedule}\n\n{localization.get_text('propose_leave_lesson', callback.from_user.language_code)}"
    await callback.message.answer(answer_string)
    await callback.answer()


@router.message(TextFilter('my_lessons'))
@router.message(Command("my_lessons"))
async def cmd_my_lessons(message: Message):
    lessons_of_student = db.get_lessons_of_student(message.from_user.id)
    formated_schedule = lessonformat.format_schedule_by_day(lessons_of_student, message.from_user.language_code, False)
    if formated_schedule == '\n':
        answer_string = f"{localization.get_text('no_lessons_to_show', message.from_user.language_code)}"
    else:
        answer_string = f"{localization.get_text('your_lessons', message.from_user.language_code)}\n{formated_schedule}\n\n{localization.get_text('propose_leave_lesson', message.from_user.language_code)}"
    await message.answer(answer_string)


@router.message(Command("leave"))
async def cmd_leave_lesson(
        message: Message,
        command: CommandObject):
    if command.args is None:
        await message.answer(f"{localization.get_text('wrong_leave_format', message.from_user.language_code)}")
        return
    lesson_id = command.args
    user_id = message.from_user.id
    if not lesson_id.isdigit():
        await message.answer(localization.get_text('wrong_lesson_id', message.from_user.language_code))
        return
    res = db.unregister_student_for_lesson(user_id, lesson_id)
    if res == 'no lesson registered error':
        await message.answer(f"{localization.get_text('wrong_leave_lesson', message.from_user.language_code)}")
    if res == "can't unregister lesson":
        await message.answer(f"{localization.get_text('impossible_unregister', message.from_user.language_code)}")
    if res == 'ok':
        await message.answer(f"{localization.get_text('successful_unregister_for_lesson', message.from_user.language_code)}{lesson_id}")





