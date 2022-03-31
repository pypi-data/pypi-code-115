from the_one_api_sdk.common import BaseApi
from .model import Book


class BookApi(BaseApi):
    model = Book
    list_path = '/book'
    auth = False
