from the_one_api_sdk.book import BookApi
from the_one_api_sdk.chapter import ChapterApi
from the_one_api_sdk.character import CharacterApi
from the_one_api_sdk.common import ApiClient
from the_one_api_sdk.movie import MovieApi
from the_one_api_sdk.quote import QuoteApi

BASE_URL = 'https://the-one-api.dev/v2'


class TheOneApi:
    def __init__(self, api_key=None, base_url=BASE_URL):
        api_client = ApiClient(api_key, base_url)

        self.book = BookApi(api_client)
        self.movie = MovieApi(api_client)
        self.character = CharacterApi(api_client)
        self.quote = QuoteApi(api_client)
        self.chapter = ChapterApi(api_client)
