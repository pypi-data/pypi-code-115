from ..domain.channel import Channel
from ..domain.schemas import Insight, Result


class gRPCChannel(Channel):

    def __init__(self, url: str, api_key: str):
        self._url = url
        self._api_key = api_key

    def connect(self):
        ...

    def write(self, insight: Insight) -> Result:
        ...
