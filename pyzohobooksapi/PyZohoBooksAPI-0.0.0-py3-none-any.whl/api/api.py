import json

import requests


class API:
    @staticmethod
    def _start_connection(method, url, headers=None, params=None, data=None):
        # response = requests.request(method, url, headers=headers, data=data)
        if method.upper() == 'POST':
            return requests.post(url=url, headers=headers, params=params, data=json.dumps(data))
        elif method.upper() == 'GET':
            return requests.get(url=url, headers=headers, params=params, data=json.dumps(data))
        else:
            raise 'please enter valid method (POST, GET)'


    @staticmethod
    def _parse_response(response):
        data = json.loads(response.text)
        status = response.status_code
        return status, data
