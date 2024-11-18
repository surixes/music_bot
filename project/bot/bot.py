import logging
import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from project.bot.config import API_TOKEN
from utils import CheckUserMiddleware
from project.bot.database import get_playlists_by_genre, get_playlists_by_artist, get_playlists_by_mood

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

router = Router()

dp.message.middleware(CheckUserMiddleware())
dp.callback_query.middleware(CheckUserMiddleware())

router.message.register(F.text, )

async def main():
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())