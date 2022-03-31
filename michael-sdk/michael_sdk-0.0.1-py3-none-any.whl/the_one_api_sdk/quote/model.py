from the_one_api_sdk.common import BaseModel


class Quote(BaseModel):
    attributes_map = {
        '_id': 'id',
        'dialog': 'dialog',
        'movie': 'movie',
        'character': 'character',
    }
    id = None
    dialog = None

    @property
    def character(self):
        from the_one_api_sdk.character import CharacterApi

        return CharacterApi(self.api_client).get(self._character_id)

    @character.setter
    def character(self, value):
        self._character_id = value

    @property
    def movie(self):
        from the_one_api_sdk.movie import MovieApi

        return MovieApi(self.api_client).get(self._movie_id)

    @movie.setter
    def movie(self, value):
        self._movie_id = value

    def __repr__(self):
        return f'<Quote: {self.id}>'
