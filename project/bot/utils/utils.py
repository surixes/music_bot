import logging
from aiogram import Bot, BaseMiddleware
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from typing import Callable, Any, Awaitable
from aiogram.exceptions import TelegramBadRequest
from database import get_async_session, User
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError

class CheckUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message], Awaitable[Any]],
        event: Message,
        data: dict
    ) -> Any:
        user_id = event.from_user.id # type: ignore

        if isinstance(event, Message):
            message_text = event.text or ""

            async with get_async_session() as session:
                try:
                    result = await session.execute(select(User).where(User.user_id == user_id))
                    user = result.scalar_one_or_none()

                    if user:
                        user.last_activity = func.now()
                        await session.commit()
                except SQLAlchemyError as e:
                    logging.error(f"Error updating user last_activity: {e}")

                # Если это команда /start, проверяем на реферальный ID и сохраняем его в FSM
            if message_text.startswith("/start"):
                parts = message_text.split()
                if len(parts) > 1 and parts[1].isdigit():
                    referrer_id = int(parts[1])
                    # Сохраняем реферальный ID в состояние FSM перед проверками
                    state = data.get("state")
                    await state.update_data(referrer_id=referrer_id) # type: ignore
                    logging.info(f"Referrer ID {referrer_id} saved in middleware for user {user_id}")


        if await is_user_blocked(user_id): # type: ignore
            await event.answer("❌ Вы заблокированы и не можете пользоваться ботом\n\nПо всем вопросам обращайтесь в поддержку *@refbot_admin*.", parse_mode="Markdown")
            return
        
        if not await check_membership(event.bot, event): # type: ignore
            return
        
        return await handler(event, data) # type: ignore
         