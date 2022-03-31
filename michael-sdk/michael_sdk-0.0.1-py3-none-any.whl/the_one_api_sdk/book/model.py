from the_one_api_sdk.chapter import ChapterApi
from the_one_api_sdk.common import BaseModel


class Book(BaseModel):
    attributes_map = {
        '_id': 'id',
        'name': 'name',
    }
    id = None
    name = None

    @property
    def chapter(self):
        obj = ChapterApi(self.api_client)
        obj.list_path = f'/book/{self.id}/chapter'
        obj.auth = False
        return obj

    def __repr__(self):
        return f'<Book: {self.id}, {self.name}>'
