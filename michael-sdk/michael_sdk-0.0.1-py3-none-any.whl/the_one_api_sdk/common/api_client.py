from urllib.parse import urlencode

import requests

from .errors import UnauthorizedError, EmptyResponseError, NotFoundError


class ApiClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def get_headers(self, auth):
        headers = {
            'Content-Type': 'application/json'
        }
        if auth:
            headers['Authorization'] = f'Bearer {self.api_key}'

        return headers

    def get(self, path, params=None, filters=None, auth=True):
        query = []
        if params:
            query.append(urlencode(params))
        if filters:
            query.append('&'.join(filters))
        query = f"?{'&'.join(query)}" if query else ''

        response = requests.get(
            f'{self.base_url}{path}{query}',
            headers=self.get_headers(auth),
        )

        if response.status_code == 401:
            raise UnauthorizedError("The provided api_key is not valid")

        if response.status_code == 404:
            raise NotFoundError("Endpoint does not exist")

        if not response.text:
            raise EmptyResponseError("Empty response from the server")

        return response.json()
