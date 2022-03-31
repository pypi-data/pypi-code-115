from the_one_api_sdk.common import BaseModel


class Chapter(BaseModel):
    attributes_map = {
        '_id': 'id',
        'chapterName': 'chapter_name',
        'book': 'book'
    }
    id = None
    chapter_name = None

    _book_id = None

    @property
    def book(self):
        from the_one_api_sdk.book import BookApi

        if self._book_id:
            return BookApi(self.api_client).get(self._book_id)

    @book.setter
    def book(self, value):
        self._book_id = value

    def __repr__(self):
        return f'<Chapter: {self.id}, {self.chapter_name}>'
