import types

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from localization import localization
from aiogram import F


class TextFilter(BaseFilter):
    def __init__(self, text: str):
        self.text = text

    async def __call__(self, message: Message) -> bool:
        if type(message.text) == types.NoneType:
            return False
        words = {word.lower() for word in localization.get_text(self.text)}
        return message.text.lower() in words
