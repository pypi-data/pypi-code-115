from the_one_api_sdk.common import BaseModel
from the_one_api_sdk.quote import QuoteApi


class Character(BaseModel):
    attributes_map = {
        '_id': 'id',
        'name': 'name',
        'height': 'height',
        'race': 'race',
        'gender': 'gender',
        'birth': 'birth',
        'spouse': 'spouse',
        'death': 'death',
        'realm': 'realm',
        'hair': 'hair',
        'wikiUrl': 'wiki_url'
    }
    id = None
    name = None
    height = None
    race = None
    gender = None
    birth = None
    spouse = None
    death = None
    realm = None
    hair = None
    wiki_url = None

    @property
    def quote(self):
        obj = QuoteApi(self.api_client)
        obj.list_path = f'/character/{self.id}/quote'
        return obj

    def __repr__(self):
        return f'<Character: {self.id}, {self.name}>'
