import json

from unittest.mock import patch, Mock

from the_one_api_sdk.common.errors import NoSuchItemError
from .base import BaseTestCase


@patch('requests.get')
class TestBook(BaseTestCase):
    def test_get_book(self, get):
        resp = {
            'docs': [
                {
                    '_id': '5cf5805fb53e011a64671582',
                    'name': 'The Fellowship Of The Ring'
                },
            ],
            'total': 1,
            'limit': 1000,
            'offset': 0,
            'page': 1,
            'pages': 1
        }
        text = json.dumps(resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: resp)

        book = self.api.book.get('5cf5805fb53e011a64671582')
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book/5cf5805fb53e011a64671582',
            headers={
                'Content-Type': 'application/json'
            }
        )
        self.assertEqual(book.id, resp['docs'][0]['_id'])
        self.assertEqual(book.name, resp['docs'][0]['name'])

    def test_get_non_existing_book(self, get):
        resp = {
            'docs': [],
            'total': 0,
            'limit': 1000,
            'offset': 0,
            'page': 1,
            'pages': 1
        }
        text = json.dumps(resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: resp)

        with self.assertRaises(NoSuchItemError):
            self.api.book.get('5cf5805fb53e011a64671582')

    def test_get_books(self, get):
        resp = {
            'docs': [
                {
                    '_id': '5cf5805fb53e011a64671582',
                    'name': 'The Fellowship Of The Ring'
                },
                {
                    '_id': '5cf5805fb53e011a64671582',
                    'name': 'The Two Towers'
                },
            ],
            'total': 2,
            'limit': 1000,
            'offset': 0,
            'page': 1,
            'pages': 1
        }
        text = json.dumps(resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: resp)

        books = self.api.book.list()
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book',
            headers={
                'Content-Type': 'application/json'
            }
        )
        self.assertEqual(len(books._items), 2)
        self.assertEqual(books[0].id, resp['docs'][0]['_id'])
        self.assertEqual(books[0].name, resp['docs'][0]['name'])
        self.assertEqual(books[1].id, resp['docs'][1]['_id'])
        self.assertEqual(books[1].name, resp['docs'][1]['name'])

    def test_get_book_chapters(self, get):
        resp = {
            'docs': [
                {
                    '_id': '5cf5805fb53e011a64671582',
                    'name': 'The Fellowship Of The Ring'
                },
            ],
            'total': 1,
            'limit': 1000,
            'offset': 0,
            'page': 1,
            'pages': 1
        }
        text = json.dumps(resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: resp)

        book = self.api.book.get('5cf5805fb53e011a64671582')

        resp = {
            'docs': [
                {
                    '_id': '6091b6d6d58360f988133b8b',
                    'chapterName': 'A Long-expected Party'
                },
                {
                    '_id': '6091b6d6d58360f988133b8c',
                    'chapterName': 'The Shadow of the Past'
                }
            ],
            'total': 22,
            'limit': 2,
            'offset': 0,
            'page': 1,
            'pages': 11
        }
        text = json.dumps(resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: resp)

        chapters = book.chapter.list()
        get.assert_called_with(
            'https://the-one-api.dev/v2/book/5cf5805fb53e011a64671582/chapter',
            headers={
                'Content-Type': 'application/json'
            }
        )
        self.assertEqual(len(chapters._items), 2)
        self.assertEqual(chapters[0].id, resp['docs'][0]['_id'])
        self.assertEqual(chapters[0].chapter_name, resp['docs'][0]['chapterName'])
        self.assertEqual(chapters[1].id, resp['docs'][1]['_id'])
        self.assertEqual(chapters[1].chapter_name, resp['docs'][1]['chapterName'])
