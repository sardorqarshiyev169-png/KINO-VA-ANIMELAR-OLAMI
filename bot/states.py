from aiogram.fsm.state import State, StatesGroup


class ContentForm(StatesGroup):
    title = State()
    description = State()
    year = State()
    genre = State()
    file_id = State()
    media_type = State()


class EpisodeForm(StatesGroup):
    choose_series = State()
    episode_number = State()
    title = State()
    description = State()
    file_id = State()
    media_type = State()


class SearchForm(StatesGroup):
    query = State()


class ChannelForm(StatesGroup):
    channel_id = State()
    name = State()
    url = State()