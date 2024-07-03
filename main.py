import asyncio
import logging
from localization import localization
import sys
from os import getenv
from config_db import get_database_connection
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.formatting import Text, Bold
from config_reader import config
from aiogram import F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from handlers import user, non_user, other

bot = Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()

db = get_database_connection()


@dp.message(Command("hello"))
async def cmd_hello(message: Message):
    content = Text(
        "Hello, ",
        Bold(message.from_user.full_name),
        "\n",
        Bold(message.from_user.first_name),
        "\n",
        Bold(message.from_user.last_name),

    )
    await message.answer(
        **content.as_kwargs()
    )


async def main():
    dp.include_routers(user.router, non_user.router, other.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
