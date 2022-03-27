from abc import ABC, abstractmethod
from typing import Union


class Proxy:
    def __init__(
        self,
        address: str,
        port: int,
        protocol: str = "http",
        username: str = None,
        password: str = None,
    ):
        self.address = address
        self.port = port
        self.protocol = protocol
        self.username = username
        self.password = password


class ProxyAdapter(ABC):
    def __init__(self, regeneration_limit: int):
        self._proxy: Union[Proxy, None] = None
        self._regeneration_limit: int = regeneration_limit

    def get_proxy(self) -> Proxy:
        if self._proxy is None:
            self._proxy = self.new_proxy()
        return self._proxy

    def new_proxy(self) -> Proxy:
        proxy: Union[Proxy, None] = None
        for i in range(self._regeneration_limit):
            proxy = self._gen_proxy()
            if proxy != self._proxy:
                break

        if proxy is None:
            raise ValueError("Could not choose a new proxy")

        if proxy == self._proxy:
            raise ValueError("Proxy regeneration limit exceeded")

        self._proxy = proxy
        return self.get_proxy()

    @abstractmethod
    def _gen_proxy(self) -> Union[Proxy, None]:  # pragma: no cover
        pass
