# Copyright 2022 The CRISPRbrain.org Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import gzip
import hashlib
import json
import logging
from io import BytesIO
from typing import Dict

import pandas as pd
import requests
import requests_cache

_SERVER = "https://crisprbrain.org"
_CLIENT_ID = "92f263647c43525d3e4f181aa7e348f26e32129c0f827321d9261cc9765c56c0"


class Screen:
    def __init__(self, screen):
        self.__session = requests_cache.CachedSession("__crisprbrain")
        self.__screen = screen
        self.__data_frame = None
        self.__metadata = screen["metadata"]

    def to_data_frame(self) -> pd.DataFrame:
        """Returns the screen as a pandas DataFrame. May read the data
        locally from the cache. """
        if self.__data_frame is None:
            self.__get_screen()
        return self.__data_frame.copy()

    @property
    def metadata(self) -> Dict[str, str]:
        """Returns the screen metadata."""
        return self.__metadata

    def __get_screen(self):
        try:
            data_response = self.__session.get(self.__screen["download_url"])
            data_response.raise_for_status()

            hash_response = self.__session.get(
                self.__screen["hash_download_url"])
            hash_response.raise_for_status()

            if hashlib.sha512(data_response.content).hexdigest() != \
                    hash_response.content.decode():
                self.__session.cache.clear()
                raise ConnectionError("Hash Summary Check Fails.")

            csv_text = gzip.decompress(data_response.content)
            df = pd.read_pickle(BytesIO(csv_text))
            self.__data_frame = df
        except Exception as ex:
            logging.error(ex)
            self.__session.cache.clear()
            raise ConnectionError(
                "Invalid response from the server. Try again.")

    def __str__(self) -> str:
        return str.join("\n",
                        [f"{key}: {value}" for key, value in
                         self.metadata.items()])


class Client:
    def __init__(self):
        self.__client_id = _CLIENT_ID
        self.__url = _SERVER
        self.__api_version = 0
        self.__screens = None

    @property
    def screens(self) -> Dict[str, Screen]:
        """Returns the list of available screens on CRISPRbrain.org."""
        if self.__screens is None:
            response = requests.post(f"{self.__url}/api/screens",
                                     data={
                                         "client_id": self.__client_id})
            response.raise_for_status()
            json_text = gzip.decompress(response.content).decode()
            screens = json.loads(json_text)
            if type(screens) is not dict or "__version" not in screens:
                raise ConnectionError(
                    "Invalid response from the server. Try again.")

            if int(screens["__version"]) > self.__api_version:
                raise SystemError(
                    ("Your CRISPRbrain client must be updated: "
                     "pip install --upgrade crisprbrain"
                     ))

            for name, data in screens.items():
                if not name.startswith("__") and "metadata" not in data:
                    raise ConnectionError(
                        "Invalid response from the server. Try again.")

            self.__screens = screens

        ret = {}
        for name, data in self.__screens.items():
            if name.startswith("__"):
                continue
            ret[name] = Screen(data)
        return ret

    @staticmethod
    def _clear_cache():
        """Clears all cache data."""
        requests_cache.CachedSession("__crisprbrain").cache.clear()
