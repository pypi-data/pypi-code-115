from the_one_api_sdk.common import BaseApi
from .model import Quote


class QuoteApi(BaseApi):
    model = Quote
    list_path = '/quote'
    auth = True
