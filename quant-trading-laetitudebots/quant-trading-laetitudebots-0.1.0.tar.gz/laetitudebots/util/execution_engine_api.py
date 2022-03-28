# -*- encoding: utf-8 -*-

import json

import requests


class ExecutionEngineAPI:
    def __init__(self, url):
        self.url = url
        self.headers = {'x-access-token': None}

    def authenticate(self, username, password):
        endpoint = f'{self.url}/api/user/authenticate'
        dto = {'username': username, 'password': password}
        auth_resp = requests.post(endpoint, data=json.dumps(dto)).json()
        self.headers['x-access-token'] = auth_resp['result']['token']

        return auth_resp

    def get_status(self, exec_id):
        endpoint = f'{self.url}/api/execution?exec_id={exec_id}'
        status_resp = requests.get(endpoint, headers=self.headers).json()

        return status_resp['result']['exec_status']

    def submit_execution(
        self, exchange, execution_type, api_key, api_secret, params
    ):
        endpoint = f'{self.url}/api/execution'
        dto = {
            'exchange': exchange,
            'execution': execution_type,
            'api_key': api_key,
            'api_secret': api_secret,
            'params': params,
        }

        execute_resp = requests.post(
            endpoint, headers=self.headers, data=json.dumps(dto)
        ).json()

        exec_id = execute_resp['result']['exec_id']

        return exec_id

    def cancel_execution(self, exec_id):
        endpoint = f'{self.url}/api/execution/cancel'
        dto = {'exec_id': exec_id}

        cancel_resp = requests.post(
            endpoint, headers=self.headers, data=json.dumps(dto)
        ).json()

        return cancel_resp
