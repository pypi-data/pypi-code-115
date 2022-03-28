import requests

import json

class API:
    def __init__(self):
        self.api_key = None

    def auth(self, api_key):
        self.api_key = api_key

    def create_txn(self, txn):
        headers = {'api-key', self.api_key}
        payload = json.dumps(txn)

        # TODO: throw exceptions for bad data
        if 'uuid' not in payload or not type(payload['uuid'], str):
            raise ValueError('Missing field(s) or invalid type, please see documentation <link>.')

        r = requests.post('https://api.smilecoin.us/api/v1/persist/platform/txn', headers=headers, json=payload)

        # TODO: if r.status_code != 201, throw exception

        return {'status_code': r.status_code, 'response': r.content}

    def receive(self, txn):
        headers = {'api-key', self.api_key}
        payload = json.dumps(txn)

        # TODO: throw exceptions for bad data
        if 'txn_id' not in payload or not type(payload['txn_id'], int):
            raise ValueError('Missing field(s) or invalid type, please see documentation <link>.')

        r = requests.post('https://api.smilecoin.us/api/v1/smile/receive', headers=headers, json=payload)

        # TODO: if r.status_code != 201, throw exception

        return {'status_code': r.status_code, 'response': r.content}


    def send(self, txn):
        headers = {'api-key', self.api_key}
        payload = json.dumps(txn)

        # TODO: throw exceptions for bad data
        if 'txn_id' not in payload or not type(payload['txn_id'], int):
            raise ValueError('Missing field(s) or invalid type, please see documentation <link>.')

        r = requests.post('https://api.smilecoin.us/api/v1/smile/pay', headers=headers, json=payload)

        # TODO: if r.status_code != 201, throw exception

        return {'status_code': r.status_code, 'response': r.content}