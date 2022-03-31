from the_one_api_sdk.common import BaseApi
from .model import Movie


class MovieApi(BaseApi):
    model = Movie
    list_path = '/movie'
    auth = True
