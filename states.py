from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_movie_code = State()
    waiting_anime_code = State()


class AdminStates(StatesGroup):
    waiting_movie_video = State()
    waiting_movie_code = State()
    waiting_anime_video = State()
    waiting_anime_code = State()
    waiting_broadcast = State()
    waiting_channel_input = State()
    waiting_delete_movie_code = State()
    waiting_delete_anime_code = State()
