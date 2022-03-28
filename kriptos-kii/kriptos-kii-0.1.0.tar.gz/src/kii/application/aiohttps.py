from typing import Dict

import aiohttp

from ..domain.aiochannel import AioChannel
from ..domain.schemas import Insight, Result


class AioHTTPChannel(AioChannel):

    def __init__(self, url: str, api_key: str):
        self._url = url
        self._api_key = api_key

    async def connect(self):
        ...

    async def write(self, insight: Insight) -> Result:
        headers = {'x-api-key': self._api_key}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f"{self._url}", json=insight.to_dict()) as response:
                if response.status == 200:
                    return Result(await response.json())
