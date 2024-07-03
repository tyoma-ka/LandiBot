from aiogram.filters import BaseFilter
from aiogram.types import Message
from config_db import get_database_connection


class UserFilter(BaseFilter):
    def __init__(self, user_type: str):
        self.user_type = user_type

    async def __call__(self, message: Message) -> bool:
        if self.user_type == 'User':
            return db.check_user_by_id(message.from_user.id)
        if self.user_type == 'NonUser':
            return not db.check_user_by_id(message.from_user.id)
        if self.user_type == 'Teacher':
            return db.check_teacher_by_id(message.from_user.id)
        if self.user_type == 'Student':
            return not db.check_teacher_by_id(message.from_user.id)


db = get_database_connection()
