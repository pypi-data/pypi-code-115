from the_one_api_sdk.common import BaseApi
from .model import Character


class CharacterApi(BaseApi):
    model = Character
    list_path = '/character'
    auth = True
