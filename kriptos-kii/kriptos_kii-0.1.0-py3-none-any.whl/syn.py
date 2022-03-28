from .application.https import HTTPChannel
from .config import KRIPTOS_SERVICE_URL
from .domain.channel import Channel


class Client:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def connect(self) -> Channel:
        channel = HTTPChannel(KRIPTOS_SERVICE_URL, self._api_key)
        channel.connect()
        return channel
