from the_one_api_sdk.common import BaseApi
from .model import Chapter


class ChapterApi(BaseApi):
    model = Chapter
    list_path = '/chapter'
    auth = True
