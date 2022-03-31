import json
from unittest.mock import patch, Mock

from the_one_api_sdk.common.errors import *
from .base import BaseTestCase


@patch('requests.get')
class TestApi(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.resp = {'docs': []}

    def test_unauthorized_request(self, get):
        get.return_value = Mock(status_code=401)

        with self.assertRaises(UnauthorizedError):
            self.api.book.list()

    def test_endpoint_not_found(self, get):
        get.return_value = Mock(status_code=404)

        with self.assertRaises(NotFoundError):
            self.api.book.get('not-exist')

    def test_empty_response(self, get):
        get.return_value = Mock(status_code=200, text='')

        with self.assertRaises(EmptyResponseError):
            self.api.book.list()

    def test_get_objects_with_page(self, get):
        text = json.dumps(self.resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: self.resp)

        self.api.book.list(page=2)
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book?page=2',
            headers={
                'Content-Type': 'application/json'
            }
        )

    def test_get_objects_with_limit(self, get):
        text = json.dumps(self.resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: self.resp)

        self.api.book.list(limit=5)
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book?limit=5',
            headers={
                'Content-Type': 'application/json'
            }
        )

    def test_get_objects_with_offset(self, get):
        text = json.dumps(self.resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: self.resp)

        self.api.book.list(offset=10)
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book?offset=10',
            headers={
                'Content-Type': 'application/json'
            }
        )

    def test_get_objects_with_sort(self, get):
        text = json.dumps(self.resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: self.resp)

        self.api.book.list(sort='name')
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book?sort=name%3Aasc',
            headers={
                'Content-Type': 'application/json'
            }
        )

    def test_get_objects_with_sort_desc(self, get):
        text = json.dumps(self.resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: self.resp)

        self.api.book.list(sort='-name')
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book?sort=name%3Adesc',
            headers={
                'Content-Type': 'application/json'
            }
        )

    def test_get_objects_with_filters(self, get):
        text = json.dumps(self.resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: self.resp)

        self.api.book.list(filters=['name=Gandalf', 'race!=Hobbit'])
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book?name=Gandalf&race!=Hobbit',
            headers={
                'Content-Type': 'application/json'
            }
        )

    def test_get_objects_with_all_parameters(self, get):
        text = json.dumps(self.resp)
        get.return_value = Mock(status_code=200, text=text, json=lambda: self.resp)

        self.api.book.list(
            page=2,
            limit=2,
            offset=2,
            sort='-name',
            filters=['name=Gandalf', 'race!=Hobbit']
        )
        get.assert_called_once_with(
            'https://the-one-api.dev/v2/book?limit=2&offset=2&page=2&sort=name%3Adesc&name=Gandalf&race!=Hobbit',
            headers={
                'Content-Type': 'application/json'
            }
        )
