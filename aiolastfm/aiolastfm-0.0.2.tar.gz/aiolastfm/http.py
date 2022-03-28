# Future
from __future__ import annotations

# Standard Library
import asyncio
import logging

# Packages
import aiohttp

# My stuff
from .exceptions import _EXCEPTION_MAPPING, HTTPException, InvalidResponse
from .types.common import Parameters, ResponseData
from .types.http import APIMethod, Headers, HTTPMethod
from .utilities import MISSING, json_or_text


__all__ = (
    "HTTPClient",
)

__log__: logging.Logger = logging.getLogger("aiolastfm.http")


class HTTPClient:

    _BASE_URL: str = "https://ws.audioscrobbler.com/2.0/"
    _USER_AGENT: str = f"aiolastfm/0.0.2 (https://github.com/Axelware/aiolastfm)"
    _HEADERS: Headers = {
        "User-Agent": _USER_AGENT,
    }

    def __init__(
        self,
        *,
        client_key: str,
        client_secret: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:

        self._client_key: str = client_key
        self._client_secret: str | None = client_secret
        self._session: aiohttp.ClientSession | None = session

    def __repr__(self) -> str:
        return "<aiolastfm.HTTPClient>"

    # Private methods

    async def _get_session(self) -> aiohttp.ClientSession:

        if not self._session:
            self._session = aiohttp.ClientSession()

        return self._session

    async def _request(
        self,
        _method: HTTPMethod, /,
        *,
        method: APIMethod,
        **parameters: str
    ) -> ResponseData:

        session = await self._get_session()

        params: Parameters = {
            "format":  "json",
            "api_key": self._client_key,
            "method":  method,
        }
        params.update(parameters)

        response: aiohttp.ClientResponse = MISSING
        data: ResponseData | str = MISSING

        for tries in range(3):

            try:

                async with session.request(
                        _method, url=self._BASE_URL,
                        params=params,
                        headers=self._HEADERS
                ) as response:

                    data = await json_or_text(response)

                    if isinstance(data, str):
                        raise InvalidResponse

                    if code := data.get("error"):
                        raise _EXCEPTION_MAPPING[code](response, data)

                    if 200 <= response.status < 300:
                        return data

                    await asyncio.sleep(1 + tries * 2)
                    continue

            except OSError as error:
                if tries < 2 and error.errno in (54, 10054):
                    await asyncio.sleep(1 + tries * 2)
                    continue
                raise

        assert not isinstance(data, str)
        raise HTTPException(response, data=data)
