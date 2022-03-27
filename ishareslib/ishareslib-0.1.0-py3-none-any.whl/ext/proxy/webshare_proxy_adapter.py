from random import choice
from typing import Union

from requests import get

from ishareslib.core.proxy_adapter import Proxy, ProxyAdapter


class WebShareProxyAdapter(ProxyAdapter):
    def __init__(
        self,
        key: str,
        page: Union[int, None] = None,
        host: str = "proxy.webshare.io/api",
        regeneration_limit: int = 3,
    ):
        super().__init__(regeneration_limit=regeneration_limit)
        self._key: str = key
        self._page: Union[int, None] = page
        self._host: str = host
        self._proxies: list[Proxy] = []

    def new_proxy(self) -> Proxy:
        self._before_new_proxy()
        return super().new_proxy()

    def _before_new_proxy(self) -> None:
        if len(self._proxies) == 0:
            self._get_proxy_list(
                "https://%s/proxy/list/?page=%d" % (self._host, self._page or 1)
            )

    def _gen_proxy(self) -> Union[Proxy, None]:
        proxies: list[Proxy] = self._proxies
        if self._proxy is not None:
            proxies.remove(self._proxy)
        if len(proxies) == 0:
            return None
        return choice(proxies)

    def _get_proxy_list(self, url: str):
        response = get(url, headers={"Authorization": "Token %s" % self._key}).json()
        for result in response["results"]:
            if result["valid"]:
                self._proxies.append(
                    Proxy(
                        address=result["proxy_address"],
                        port=result["ports"]["http"],
                        username=result["username"],
                        password=result["password"],
                    )
                )

        if self._page is None and response["next"] is not None:
            self._get_proxy_list("https://%s" % response["next"])
