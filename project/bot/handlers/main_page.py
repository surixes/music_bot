import logging
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from database import User, get_async_session 
from aiogram.filters import Command
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

router = Router()

#class Registration(StatesGroup):

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await message.answer("Привет! Я помогу тебе найти малоизвестных исполнителей и плейлисты на любой вкус.", parse_mode="Markdown")
    await show_main_menu(message)

async def show_main_menu(message: Message):
    genre = KeyboardButton(text="По жанру", callback_query="genre")
    artist = KeyboardButton(text="По исполнителю", callback_query="artist")
    mood = KeyboardButton(text="По настроению", callback_query="mood")
    dayliplaylists = KeyboardButton(text="Плейлисты дня", callback_query="dayliplaylists")
    keyboard = ReplyKeyboardMarkup(keyboard=[[genre, artist, mood], [dayliplaylists]], resize_keyboard=True)

    await message.answer("*Выберите категорию:*", reply_markup=keyboard, parse_mode="Markdown")


# Обработка выбора жанра
@router.callback_query(F.text == "genre")
async def genre_menu(callback_query: CallbackQuery):
    # Получаем список жанров из базы данных
    genres = ["Рок", "Поп", "Джаз", "Электронная музыка", "Рэп", "Фонк", "Другое"]
    keyboard = InlineKeyboardBuilder()
    for genre in genres:
        keyboard.button(text=genre, callback_data=f"genre_{genre}")
    await callback_query.message.edit_text("Выбери жанр:", reply_markup=keyboard.as_markup())

@router.callback_query(lambda callback_query: callback_query.data.startswith("genre_"))
async def show_genre_playlists(callback_query: CallbackQuery):
    genre = callback_query.data.split("_")[1]
    playlists = get_playlists_by_genre(genre)
    await send_playlists(callback_query, playlists)

# Подобный обработчик для исполнителей
@router.callback_query(lambda callback_query: callback_query.data == "artist")
async def artist_menu(callback_query: CallbackQuery):
    artists = ["Исполнитель 1", "Исполнитель 2", "Исполнитель 3"]  # Получить из базы
    keyboard = InlineKeyboardBuilder()
    for artist in artists:
        keyboard.button(text=artist, callback_data=f"artist_{artist}")
    await callback_query.message.edit_text("Выбери исполнителя:", reply_markup=keyboard.as_markup())

@router.callback_query(lambda callback_query: callback_query.data.startswith("artist_"))
async def show_artist_playlists(callback_query: CallbackQuery):
    artist = callback_query.data.split("_")[1]
    playlists = get_playlists_by_artist(artist)
    await send_playlists(callback_query, playlists)

# Обработка настроения
@router.callback_query(lambda callback_query: callback_query.data == "mood")
async def mood_menu(callback_query: types.CallbackQuery):
    moods = ["Веселое", "Спокойное", "Энергичное"]  # Пример настроений
    keyboard = InlineKeyboardBuilder()
    for mood in moods:
        keyboard.button(text=mood, callback_data=f"mood_{mood}")
    await callback_query.message.edit_text("Выбери настроение:", reply_markup=keyboard.as_markup())

@router.callback_query(lambda callback_query: callback_query.data.startswith("mood_"))
async def show_mood_playlists(callback_query: types.CallbackQuery):
    mood = callback_query.data.split("_")[1]
    playlists = get_playlists_by_mood(mood)
    await send_playlists(callback_query, playlists)

async def send_playlists(callback_query, playlists):
    if playlists:
        for playlist in playlists:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="Сохранить в Яндекс.Музыке", url=playlist['yandex_url'])
            keyboard.button(text="Поделиться", callback_data=f"share_{playlist['id']}")
            await callback_query.message.answer(
                f"Плейлист: {playlist['title']}\n{playlist['description']}",
                reply_markup=keyboard.as_markup()
            )
    else:
        await callback_query.message.answer("Нет доступных плейлистов для выбранной категории.")

# Функция обработки кнопки "Поделиться"
@router.callback_query(lambda callback_query: callback_query.data.startswith("share_"))
async def share_playlist(callback_query: types.CallbackQuery):
    playlist_id = callback_query.data.split("_")[1]
    # Здесь можно реализовать логику для создания ссылки на плейлист или просто пересылки сообщения
    await callback_query.message.answer("Плейлист можно переслать друзьям или сохранить себе.")