from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from localization import localization
from aiogram import F


class TextFilter(BaseFilter):
    def __init__(self, text: str):
        self.text = text

    async def __call__(self, message: Message) -> bool:
        return message.text.lower() == localization.get_text(self.text, message.from_user.language_code).lower()
