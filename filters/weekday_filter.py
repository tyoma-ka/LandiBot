from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class WeekdayFilter(BaseFilter):
    def __init__(self, reverse=False):
        self.weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        self.reverse = reverse

    async def __call__(self, callback: CallbackQuery) -> bool:
        if callback.data in self.weekdays:
            return not self.reverse
        return self.reverse
