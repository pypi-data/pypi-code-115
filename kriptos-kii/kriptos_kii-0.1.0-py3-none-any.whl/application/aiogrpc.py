from ..domain.aiochannel import AioChannel
from ..domain.schemas import Insight, Result


class AiogRPCChannel(AioChannel):

    def __init__(self, url: str, api_key: str):
        self._url = url
        self._api_key = api_key

    async def connect(self):
        ...

    async def write(self, insight: Insight) -> Result:
        ...
