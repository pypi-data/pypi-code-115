from .application.aiohttps import AioHTTPChannel
from .config import KRIPTOS_SERVICE_URL
from .domain.aiochannel import AioChannel


class Client:
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def connect(self) -> AioChannel:
        channel = AioHTTPChannel(KRIPTOS_SERVICE_URL, self._api_key)
        await channel.connect()
        return channel
