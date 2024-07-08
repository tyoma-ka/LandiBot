import datetime

from aiogram import Router, F
from aiogram import Bot, Dispatcher
from aiogram.filters import BaseFilter
from aiogram.filters import Command, StateFilter, CommandObject
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, ContentType, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey

import formating.lessonformat
from config_db import get_database_connection
from filters.user_filter import UserFilter
from filters.weekday_filter import WeekdayFilter
from filters.timetable_filter import TimetableFilter
from filters.text_filter import TextFilter
from aiogram.fsm.context import FSMContext
from formating import lessonformat, timeformat
import aiohttp
import ssl
import os
import calendar

from keyboards import kb_user
from localization import localization


class SendTimetable(StatesGroup):
    choosing_way = State()
    sending_timetable = State()
    sending_date = State()
    sending_time = State()
    sending_name = State()
    sending_max = State()
    asking_to_continue = State()


class ChooseWeekday(StatesGroup):
    choosing_weekday = State()
    delete_weekday = State()


class ChooseLessonNumber(StatesGroup):
    choosing_lesson_number = State()
    delete_lesson_number = State()


class ShowStudentsForLesson(StatesGroup):
    choosing_lesson_number = State()


class ChooseLessonEditNumber(StatesGroup):
    choosing_lesson_number = State()
    choosing_what_to_edit = State()
    waiting_for_datetime = State()
    waiting_for_name = State()
    waiting_for_max = State()


router = Router()
router.message.filter(
    UserFilter(user_type="Teacher")
)

db = get_database_connection()
storage = MemoryStorage()


@router.message(Command(commands=["cancel"]))
@router.message(TextFilter('cancel_name'))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(localization.get_text('cancel', message.from_user.language_code))


@router.message(StateFilter(None), Command("start"))
async def cmd_start(message: Message):
    await message.answer(localization.get_text('hey_teacher', message.from_user.language_code),
                         reply_markup=kb_user.make_teacher_keyboard(message.from_user.language_code))


@router.message(StateFilter(None), TextFilter('info'))
@router.message(StateFilter(None), Command("info"))
async def cmd_start(message: Message):
    await message.answer(localization.get_text('teacher_info', message.from_user.language_code),
                         reply_markup=kb_user.make_teacher_keyboard(message.from_user.language_code))


@router.message(StateFilter(None), TextFilter('add_timetable'))
@router.message(StateFilter(None), Command("add_timetable"))
async def cmd_add_timetable(message: Message, state: FSMContext):
    await message.answer(localization.get_text('choosing_way', message.from_user.language_code),
                         reply_markup=kb_user.get_choosing_way_keyboard(message.from_user.language_code))
    await state.set_state(SendTimetable.choosing_way)


@router.callback_query(SendTimetable.choosing_way, TimetableFilter('by_file'))
async def by_file(
        callback: CallbackQuery,
        state: FSMContext):
    await callback.message.answer(localization.get_text('send_csv', callback.from_user.language_code))
    await state.set_state(SendTimetable.sending_timetable)
    await callback.answer()


@router.callback_query(TimetableFilter('manual'))
async def manual(
        callback: CallbackQuery,
        state: FSMContext):
    await callback.message.answer(localization.get_text('send_date', callback.from_user.language_code))
    await state.set_state(SendTimetable.sending_date)
    await callback.answer()


@router.message(SendTimetable.sending_date)
async def send_date(
        message: Message,
        state: FSMContext):
    date_object = timeformat.parse_datetime_object(message.text, "%Y-%m-%d")
    if not date_object:
        await message.answer(localization.get_text('wrong_date', message.from_user.language_code))
        return
    if not timeformat.check_time_is_future(message.text, "%Y-%m-%d"):
        await message.answer(localization.get_text('date_in_past', message.from_user.language_code))
        return
    storage_data = {"date": date_object.date()}
    await state.update_data(storage_data)
    await message.answer(localization.get_text('send_time', message.from_user.language_code))
    await state.set_state(SendTimetable.sending_time)


@router.message(SendTimetable.sending_time)
async def send_time(
        message: Message,
        state: FSMContext):
    time_object = timeformat.parse_datetime_object(message.text, "%H:%M")
    if not time_object:
        await message.answer(localization.get_text('wrong_time', message.from_user.language_code))
        return
    storage_data = await state.get_data()
    storage_data["time"] = time_object.time()
    await state.update_data(storage_data)
    await message.answer(localization.get_text('send_name', message.from_user.language_code))
    await state.set_state(SendTimetable.sending_name)


@router.message(SendTimetable.sending_name)
async def send_name(
        message: Message,
        state: FSMContext):
    storage_data = await state.get_data()
    storage_data["name"] = message.text
    await state.update_data(storage_data)
    await message.answer(localization.get_text('send_max', message.from_user.language_code))
    await state.set_state(SendTimetable.sending_max)


@router.message(SendTimetable.sending_max)
async def send_max_number(
        message: Message,
        state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer(localization.get_text('wrong_max_number', message.from_user.language_code))
        return
    storage_data = await state.get_data()
    storage_data["max"] = message.text

    res = db.add_lesson(
        datetime.datetime.combine(
                storage_data["date"], storage_data["time"]).isoformat(),
        storage_data["name"],
        storage_data["max"])
    if res != 'ok':
        await message.answer(f"{localization.get_text('error', message.from_user.language_code)}{res}")
        return
    await state.update_data({})
    await message.answer(localization.get_text('successful_lesson_reg', message.from_user.language_code), reply_markup=kb_user.get_continue_keyboard(message.from_user.language_code))
    await state.clear()


@router.message(SendTimetable.sending_timetable, F.document)
async def download_timetable(message: Message, state: FSMContext):
    document = message.document
    if document.mime_type == 'text/csv':
        file_info = await message.bot.get_file(document.file_id)
        file_path = file_info.file_path

        async with aiohttp.ClientSession() as session:
            file_url = f'https://api.telegram.org/file/bot{message.bot.token}/{file_path}'
            async with session.get(file_url, ssl=False) as response:
                if response.status == 200:
                    file_data = await response.read()
                    res = db.add_timetable(file_data)
                    if res != 'ok':
                        await message.reply(f"{localization.get_text('error', message.from_user.language_code)}{res}")
                    else:
                        await message.reply(localization.get_text('timetable_added', message.from_user.language_code))
                        await state.clear()
                else:
                    await message.reply(f"{localization.get_text('error', message.from_user.language_code)}{localization.get_text('loading_error', message.from_user.language_code)}")
    else:
        await message.reply(localization.get_text('send_csv', message.from_user.language_code))


@router.message(SendTimetable.sending_timetable)
async def incorrect_timetable(message: Message, state: FSMContext):
    await message.answer(f"{localization.get_text('send_csv', message.from_user.language_code)}\n{localization.get_text('propose_cancel', message.from_user.language_code)}")


@router.message(StateFilter(None), TextFilter('students'))
@router.message(StateFilter(None), Command("students"))
async def get_users(message: Message):
    data = db.get_all_students()
    await message.answer(f"{localization.get_text('students_list', message.from_user.language_code)}\n{data}")


@router.message(StateFilter(None), Command("kick"))
async def kick(
        message: Message,
        command: CommandObject):
    if command.args is None:
        await message.answer(f"{localization.get_text('no_user_id_for_delete', message.from_user.language_code)}")
        return
    user_id = command.args
    if user_id == str(message.from_user.id):
        await message.answer(f"{localization.get_text('you_suicide', message.from_user.language_code)}")
    res = db.delete_user_by_id(user_id)
    if res == 'no user error':
        await message.answer(f"{localization.get_text('no_such_user_id', message.from_user.language_code)}")
    elif res == 'ok':
        await message.answer(f"{localization.get_text('user_has_been_deleted', message.from_user.language_code)} {user_id}")


@router.message(StateFilter(None), TextFilter('timetable'))
@router.message(StateFilter(None), Command("timetable"))
async def cmd_view_timetable(message: Message):
    data = lessonformat.format_schedule_by_day(db.get_timetable_by_week(), message.from_user.language_code)
    # one more week forward
    data += lessonformat.format_schedule_by_day(db.get_timetable_by_week(1), message.from_user.language_code)
    await message.answer(
        f"{localization.get_text('teacher_timetable', message.from_user.language_code)}\n{data}")


@router.message(StateFilter(None), TextFilter('students_for_lesson'))
@router.message(StateFilter(None), Command("show"))  # TODO: сделать нормальное определение ошибок.не показывать что попало
async def cmd_get_students_for_lesson(
        message: Message,
        state: FSMContext):
    await message.answer(localization.get_text('ask_show_lesson_number', message.from_user.language_code))
    await state.set_state(ShowStudentsForLesson.choosing_lesson_number)


@router.message(ShowStudentsForLesson.choosing_lesson_number)
async def get_students_for_lesson(
        message: Message,
        state: FSMContext):
    lesson_id = message.text

    # lesson = db.get_lesson_by_id(lesson_id)
    #     if not lesson:
    #         await message.answer(f"{localization.get_text('wrong_lesson_id', message.from_user.language_code)}")
    #         return
    #     lesson = lesson[0]
    #     storage_data = {"lesson": lesson}
    #     await state.update_data(storage_data)
    #     await message.answer(
    #             text=f"{localization.get_text('are_you_sure_delete_lesson', message.from_user.language_code)}\n📆 {localization.get_text(timeformat.get_weekday(lesson[1]).lower(), message.from_user.language_code)}\n{lessonformat.formate_lesson(lesson, message.from_user.language_code)}",
    #             reply_markup=kb_user.make_yes_no_keyboard(message.from_user.language_code))
    lesson = db.get_lesson_by_id(lesson_id)
    if not lesson:
        await message.answer(f"{localization.get_text('wrong_lesson_id', message.from_user.language_code)}")
        await state.clear()
        return
    lesson = lesson[0]
    students = db.get_students_for_lesson(lesson_id)
    if not students:
        await message.answer(f"{localization.get_text('nobody_registered', message.from_user.language_code)}\n📆 <b>{timeformat.reformat_datetime_to(lesson[1], '%Y-%m-%dT%H:%M:%S', '%d.%m')} ({localization.get_text(timeformat.get_weekday(lesson[1]).lower(), message.from_user.language_code)})</b>\n{lessonformat.formate_lesson(lesson, message.from_user.language_code)}")
        await state.clear()
        return
    formated_students = lessonformat.format_students_for_lesson(students, message.from_user.language_code)
    await message.answer(f"📆 <b>{timeformat.reformat_datetime_to(lesson[1], '%Y-%m-%dT%H:%M:%S', '%d.%m')} ({localization.get_text(timeformat.get_weekday(lesson[1]).lower(), message.from_user.language_code)})</b>\n{lessonformat.formate_lesson(lesson, message.from_user.language_code)}\n{formated_students}")
    await state.clear()


@router.message(StateFilter(None), Command("remove"))  # TODO: сделать нормальное определение ошибок.не удалять что попало
async def cmd_remove_student_from_lesson(
        message: Message,
        command: CommandObject):
    if command.args is None:
        await message.answer(f"{localization.get_text('wrong_format_remove_student_id_and_lesson', message.from_user.language_code)}")
        return
    data = command.args.split()
    if len(data) != 2:
        await message.answer(f"{localization.get_text('wrong_format_remove_student_id_and_lesson', message.from_user.language_code)}")
        return
    lesson_id, student_id = data
    db.remove_student_from_lesson(student_id, lesson_id)
    await message.answer(f"{localization.get_text('student_successfully_removed1', message.from_user.language_code)} {student_id} {localization.get_text('student_successfully_removed2', message.from_user.language_code)} {lesson_id}")


@router.message(StateFilter(None), TextFilter('remove_day'))
@router.message(StateFilter(None), Command("remove_day"))
async def cmd_remove_day(message: Message, state: FSMContext):
    await message.answer(text=f"{localization.get_text('choose_weekday', message.from_user.language_code)}",
                         reply_markup=kb_user.get_weekdays_keyboard(db.get_timetable_by_week(), message.from_user.language_code))
    await state.set_state(ChooseWeekday.choosing_weekday)


@router.callback_query(ChooseWeekday.choosing_weekday, WeekdayFilter())
async def cmd_choose_weekday(
        callback: CallbackQuery,
        state: FSMContext):
    storage_data = {"weekday": callback.data}
    await state.update_data(storage_data)
    await callback.message.answer(text=f"{localization.get_text('are_you_sure_delete_weekday', callback.from_user.language_code)} {localization.get_text(callback.data, callback.from_user.language_code)}",
                                  reply_markup=kb_user.make_yes_no_keyboard(callback.from_user.language_code))
    await state.set_state(ChooseWeekday.delete_weekday)


@router.callback_query(ChooseWeekday.delete_weekday, F.data == 'no')
async def cancel2(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(localization.get_text('weekday_deleting_cancel', callback.from_user.language_code))
    await callback.answer()


@router.callback_query(ChooseWeekday.delete_weekday, F.data == 'yes')
async def cmd_choose_weekday(
        callback: CallbackQuery,
        state: FSMContext):
    storage_data = await state.get_data()
    weekday = storage_data["weekday"]
    filtered_lessons = timeformat.get_events_for_specific_weekday(db.get_timetable_by_week(), weekday)
    db.delete_list_of_lessons(filtered_lessons)
    await state.clear()
    # TODO: shitty answer
    await callback.message.answer(f"{localization.get_text('timetable', callback.from_user.language_code)} {localization.get_text('on', callback.from_user.language_code)} {localization.get_text(weekday.lower(), callback.from_user.language_code).lower()} {localization.get_text('was_deleted', callback.from_user.language_code)}")
    await callback.answer()


@router.message(ChooseWeekday.delete_weekday)
@router.message(ChooseWeekday.choosing_weekday)
async def cmd_cancel(
        message: Message,
        state: FSMContext):
    await state.clear()
    await message.answer(localization.get_text('cancel', message.from_user.language_code))


@router.message(StateFilter(None), TextFilter('remove_lesson'))
async def cmd_remove_lesson(
        message: Message,
        state: FSMContext):
    await message.answer(localization.get_text('choose_number_to_delete', message.from_user.language_code))
    await state.set_state(ChooseLessonNumber.choosing_lesson_number)


@router.message(ChooseLessonNumber.choosing_lesson_number)
async def cmd_choose_lesson(
        message: Message,
        state: FSMContext):
    lesson_id = message.text
    if not lesson_id.isdigit():
        await message.answer(localization.get_text('wrong_lesson_id', message.from_user.language_code))
        return

    lesson = db.get_lesson_by_id(lesson_id)
    if not lesson:
        await message.answer(f"{localization.get_text('wrong_lesson_id', message.from_user.language_code)}")
        return
    lesson = lesson[0]
    storage_data = {"lesson": lesson}
    await state.update_data(storage_data)
    await message.answer(
        text=f"{localization.get_text('are_you_sure_delete_lesson', message.from_user.language_code)}\n📆 {localization.get_text(timeformat.get_weekday(lesson[1]).lower(), message.from_user.language_code)}\n{lessonformat.formate_lesson(lesson, message.from_user.language_code)}",
        reply_markup=kb_user.make_yes_no_keyboard(message.from_user.language_code))
    await state.set_state(ChooseLessonNumber.delete_lesson_number)


@router.callback_query(ChooseLessonNumber.delete_lesson_number, F.data == 'no')
async def cancel3(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(localization.get_text('lesson_deleting_cancel', callback.from_user.language_code))
    await callback.answer()


@router.callback_query(ChooseLessonNumber.delete_lesson_number, F.data == 'yes')
async def cmd_choose_weekday(
        callback: CallbackQuery,
        state: FSMContext):
    storage_data = await state.get_data()
    lesson = storage_data["lesson"]
    if not lesson:
        return await callback.answer()
    res = db.delete_lesson(lesson_id=lesson[0])
    await state.clear()
    if res == 'ok':
        await callback.message.answer(localization.get_text('successful_lesson_delete', callback.from_user.language_code))
    await callback.answer()


@router.message(StateFilter(None), TextFilter('edit_lesson'))
async def cmd_edit_lesson(
        message: Message,
        state: FSMContext):
    await message.answer(localization.get_text('ask_lesson_id', message.from_user.language_code))
    await state.set_state(ChooseLessonEditNumber.choosing_lesson_number)


@router.message(ChooseLessonEditNumber.choosing_lesson_number)
async def cmd_choose_lesson(
        message: Message,
        state: FSMContext):
    lesson_id = message.text
    if not lesson_id.isdigit():
        await message.answer(localization.get_text('wrong_lesson_id', message.from_user.language_code))
        return

    lesson = db.get_lesson_by_id(lesson_id)
    if not lesson:
        await message.answer(f"{localization.get_text('wrong_lesson_id', message.from_user.language_code)}")
        return
    lesson = lesson[0]
    storage_data = {"lesson": lesson}
    await state.update_data(storage_data)
    await message.answer(
        text=f"{localization.get_text('choose_what_to_edit', message.from_user.language_code)}",
        reply_markup=kb_user.get_choosing_update_parameter_keyboard(message.from_user.language_code))
    await state.set_state(ChooseLessonEditNumber.choosing_what_to_edit)


@router.callback_query(ChooseLessonEditNumber.choosing_what_to_edit, F.data == 'datetime')
async def edit_datetime(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(localization.get_text('write_new_datetime', callback.from_user.language_code))
    await callback.answer()
    await state.set_state(ChooseLessonEditNumber.waiting_for_datetime)


@router.callback_query(ChooseLessonEditNumber.choosing_what_to_edit, F.data == 'lesson_name')
async def edit_datetime(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(localization.get_text('write_lesson_name', callback.from_user.language_code))
    await callback.answer()
    await state.set_state(ChooseLessonEditNumber.waiting_for_name)


@router.callback_query(ChooseLessonEditNumber.choosing_what_to_edit, F.data == 'max_students')
async def edit_datetime(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(localization.get_text('write_max_students', callback.from_user.language_code))
    await callback.answer()
    await state.set_state(ChooseLessonEditNumber.waiting_for_max)


@router.message(ChooseLessonEditNumber.waiting_for_datetime)
async def send_date(message: Message, state: FSMContext):
    try:
        original_datetime = datetime.datetime.strptime(message.text, '%Y-%m-%d %H:%M')
    except ValueError:
        await message.answer(localization.get_text(localization.get_text('wrong_datetime', message.from_user.language_code), message.from_user.language_code))
        return

    if original_datetime.second == 0:
        original_datetime = original_datetime.replace(second=0)

    formatted_date_string = original_datetime.strftime('%Y-%m-%dT%H:%M:%S')

    storage_data = await state.get_data()
    lesson = storage_data["lesson"]
    if not lesson:
        return
    res = db.update_lesson(lesson_id=lesson[0], datetime=formatted_date_string)
    if res != 'ok':
        await message.answer(f"{localization.get_text('error', message.from_user.language_code)}{res}")
        return
    await message.answer(localization.get_text('successful_lesson_update', message.from_user.language_code))
    await state.clear()


@router.message(ChooseLessonEditNumber.waiting_for_name)
async def send_name(
        message: Message,
        state: FSMContext):
    name = message.text
    storage_data = await state.get_data()
    lesson = storage_data["lesson"]
    if not lesson:
        return
    res = db.update_lesson(lesson_id=lesson[0], lessonname=name)
    if res != 'ok':
        await message.answer(f"{localization.get_text('error', message.from_user.language_code)}{res}")
        return
    await message.answer(localization.get_text('successful_lesson_update', message.from_user.language_code))
    await state.clear()


@router.message(ChooseLessonEditNumber.waiting_for_max)
async def send_max(
        message: Message,
        state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer(localization.get_text('wrong_max_number', message.from_user.language_code))
        return
    storage_data = await state.get_data()
    lesson = storage_data["lesson"]
    if not lesson:
        return
    res = db.update_lesson(lesson_id=lesson[0], maxstudents=message.text)
    if res != 'ok':
        await message.answer(f"{localization.get_text('error', message.from_user.language_code)}{res}")
        return
    await message.answer(localization.get_text('successful_lesson_update', message.from_user.language_code))
    await state.clear()
