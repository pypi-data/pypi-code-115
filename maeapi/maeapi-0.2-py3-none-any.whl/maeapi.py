
from functools import partial
import os
import json
import requests
from typing import Dict
from maeapi.constants import MAE_BASE_API_BANKING_V1, MAE_BASE_API_V1, MAE_BASE_API_V2
from maeapi.helpers import get_authorization, initialize_headers, read_customer_key
from maeapi.mixins.banking import BankingMixin
from maeapi.mixins.transaction import TransactionMixin


class MAE(TransactionMixin, BankingMixin):
    def __init__(self,
                auth: str = None):
        self.auth = auth

        self.token = ""

        self._session = requests.Session()
        self._session.request = partial(self._session.request, timeout=30)


        # prepare headers
        if auth:
            try:
                if os.path.isfile(auth):
                    file = auth
                    with open(file) as json_file:
                        self.body_auth = json.load(json_file)
                else:
                    self.body_auth = json.loads(auth)

            except Exception as e:
                print(
                    "Failed loading provided credentials. Make sure to provide a string or a file path. "
                    "Reason: " + str(e))
        # verify authentication credentials work
        if auth:
            try:
                read_customer_key(self.body_auth);
            except KeyError:
                raise Exception("Your cookie is missing the required value customerKey")

    def _refresh_token(self):
        # this stage, the key exists and vaid, now try to get the enrollment
        self.headers = initialize_headers();
        endpoint = 'enrollment'
        response = self._send_enrollment_request(endpoint, self.body_auth)
        self.token = response

    def _send_enrollment_request(self, endpoint: str, body: Dict, additionalParams: str = "") -> Dict:
            response = self._session.post(MAE_BASE_API_V2 + endpoint,
                                        json=body,
                                        headers=self.headers,
                                        verify=False)

            response_text = json.loads(response.text)
            if response.status_code >= 400:
                message = "Server returned HTTP " + str(
                    response.status_code) + ": " + response.reason + ".\n"
                error = response_text.get('error', {}).get('message')
                raise Exception(message + error)
            return response_text

    def _send_request(self, endpoint: str, body: Dict, additionalParams: str = "") -> Dict:
            if self.token:
                self.headers["Authorization"] = get_authorization(self.token)
            response = self._session.post(MAE_BASE_API_V1 + endpoint,
                                        json=body,
                                        headers=self.headers,
                                        verify=False)

            response_text = json.loads(response.text)
            if response.status_code >= 400:
                message = "Server returned HTTP " + str(
                    response.status_code) + ": " + response.reason + ".\n"
                error = response_text.get('error', {}).get('message')
                raise Exception(message + error)
            return response_text

    def _send_get_request(self, endpoint: str, params: Dict = None) -> Dict:
            if self.token:
                self.headers["Authorization"] = get_authorization(self.token)

            response = self._session.get(MAE_BASE_API_V1 + endpoint,
                                        params=params,
                                        headers=self.headers,
                                        verify=False)

            response_text = json.loads(response.text)
            if response.status_code >= 400:
                message = "Server returned HTTP " + str(
                    response.status_code) + ": " + response.reason + ".\n"
                error = response_text.get('error', {}).get('message')
                raise Exception(message + error)
            return response_text

    def _send_banking_get_request(self, endpoint: str, params: Dict = None) -> Dict:
            if self.token:
                self.headers["Authorization"] = get_authorization(self.token)
                self.headers["maya-authorization"] = get_authorization(self.token)
            response = self._session.get(MAE_BASE_API_BANKING_V1 + endpoint,
                                        params=params,
                                        headers=self.headers,
                                        verify=False)

            response_text = json.loads(response.text)
            if response.status_code >= 400:
                message = "Server returned HTTP " + str(
                    response.status_code) + ": " + response.reason + ".\n"
                error = response_text.get('error', {}).get('message')
                raise Exception(message + error)
            return response_text

    def _check_auth(self):
        if not self.auth:
            raise Exception("Please provide authentication before using this function")
        if not self.token:
            self._refresh_token();
