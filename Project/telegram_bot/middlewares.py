from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

class DjangoUserMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        # Здесь можно добавить логику проверки пользователя в Django
        pass