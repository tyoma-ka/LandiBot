from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class TimetableFilter(BaseFilter):
    def __init__(self, timetable_type: str):
        self.timetable_type = timetable_type

    async def __call__(self, callback: CallbackQuery) -> bool:
        return self.timetable_type == callback.data
