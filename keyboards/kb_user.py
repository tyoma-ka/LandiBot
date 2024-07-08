import calendar

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from localization import localization
from formating import timeformat


def make_inline_start_keyboard(language) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text=localization.get_text('timetable', language),
        callback_data="timetable"),
        InlineKeyboardButton(
            text=localization.get_text('my_lessons', language),
            callback_data="my_lessons"))

    return keyboard.as_markup()


def make_start_keyboard(language) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(
            text=localization.get_text('timetable', language),
            callback_data="timetable"),
        KeyboardButton(
            text=localization.get_text('my_lessons', language),
            callback_data="my_lessons"),
        KeyboardButton(
            text=localization.get_text('join', language),
            callback_data="join"),
        KeyboardButton(
            text=localization.get_text('leave', language),
            callback_data="leave"),
        KeyboardButton(
            text=localization.get_text('info', language),
            callback_data="info"),
        KeyboardButton(
            text=localization.get_text('cancel_name2', language),
            callback_data="cancel")
    )
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)


def make_teacher_keyboard(language) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(
            text=localization.get_text('timetable', language),
            callback_data="timetable"),
        KeyboardButton(
            text=localization.get_text('add_timetable', language),
            callback_data="add_timetable"),
        KeyboardButton(
            text=localization.get_text('students', language),
            callback_data="students"),
        KeyboardButton(
            text=localization.get_text('students_for_lesson', language),
            callback_data="show"),
        KeyboardButton(
            text=localization.get_text('remove_day', language),
            callback_data="remove_day"),
        KeyboardButton(
            text=localization.get_text('remove_lesson', language),
            callback_data="remove_lesson"),
        KeyboardButton(
            text=localization.get_text('edit_lesson', language),
            callback_data="edit_lesson"),
        KeyboardButton(
            text=localization.get_text('info', language),
            callback_data="info"),
        KeyboardButton(
            text=localization.get_text('cancel_name2', language),
            callback_data="cancel")
    )
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)


def make_yes_no_keyboard(language) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=localization.get_text('yes', language),
            callback_data="yes"),
        InlineKeyboardButton(
            text=localization.get_text('no', language),
            callback_data="no"))
    return keyboard.as_markup()


def get_weekdays_keyboard(events, language) -> InlineKeyboardMarkup:
    weekdays = timeformat.get_all_weekdays(events)
    buttons = [InlineKeyboardButton(
        text=localization.get_text(day.lower(), language),
        callback_data=day.lower()) for day in weekdays]
    row_size = 2
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + row_size] for i in range(0, len(buttons), row_size)])
    return keyboard


def get_choosing_way_keyboard(language) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=localization.get_text('by_file', language),
            callback_data="by_file"),
        InlineKeyboardButton(
            text=localization.get_text('manual', language),
            callback_data="manual"))
    return keyboard.as_markup()


def get_continue_keyboard(language) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=localization.get_text('continue', language),
            callback_data="manual"))
    return keyboard.as_markup()


def get_choosing_update_parameter_keyboard(language) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(
            text=localization.get_text('datetime', language),
            callback_data="datetime"),
        InlineKeyboardButton(
            text=localization.get_text('lesson_name', language),
            callback_data="lesson_name"),
        InlineKeyboardButton(
            text=localization.get_text('max_students', language),
            callback_data="max_students")]
    row_size = 1
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + row_size] for i in range(0, len(buttons), row_size)])
    return keyboard
