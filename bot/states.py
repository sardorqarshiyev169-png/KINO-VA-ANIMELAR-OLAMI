from aiogram.fsm.state import State, StatesGroup


class ContentForm(StatesGroup):
    title = State()
    description = State()
    year = State()
    genre = State()
    file_id = State()
    media_type = State()


class EpisodeForm(StatesGroup):
    file = State()          # Admin video/document yuboradi
    choose_series = State() # Qaysi serial/animega tegishli?
    episode_number = State() # Qism raqami


class SearchForm(StatesGroup):
    query = State()


class ChannelForm(StatesGroup):
    channel_id = State()
    name = State()
    url = State()


class AdminForm(StatesGroup):
    telegram_id = State()
    first_name = State()