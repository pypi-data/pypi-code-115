import requests
from ..domain.channel import Channel
from ..domain.schemas import Result, Insight


class HTTPChannel(Channel):

    def __init__(self, url: str, api_key: str):
        self._url = url
        self._api_key = api_key

    def connect(self):
        ...

    def write(self, insight: Insight) -> Result:
        headers = {'x-api-key': self._api_key}
        response = requests.post(f"{self._url}", headers=headers, json=insight.to_dict())
        if response.status_code == 200:
            return Result(response.json())
