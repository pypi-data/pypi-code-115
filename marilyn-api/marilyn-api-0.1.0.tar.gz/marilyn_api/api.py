import json as json_
from typing import Callable, Tuple, Union, Any

from aiohttp import ClientResponse, ClientSession

from marilyn_api.exeptions import ApiError


class AsyncApi:
    def __init__(
        self,
        api_root: str,
        *,
        headers: dict = None,
        settings: dict = None,
        json_dumps: Callable = json_.dumps,
        json_loads: Callable = json_.loads
    ):
        self.api_root = api_root.rstrip("/")
        self.settings = settings or {}
        self.headers = headers or {}
        self.json_dumps = json_dumps
        self.json_loads = json_loads

    async def call_endpoint(
        self,
        endpoint,
        method=None,
        params=None,
        headers=None,
        data=None,
        json=None,
    ) -> Tuple[ClientResponse, Union[str, dict, Any]]:
        url = self.api_root + endpoint
        headers = headers or {}

        async with ClientSession(
            json_serialize=self.json_dumps, headers={**self.headers, **headers}
        ) as session:
            async with session.request(
                method, url, params=params, data=data, json=json, **self.settings
            ) as response:
                return (response, await self.process_response(response))

    async def response_to_native(
        self, response: ClientResponse
    ) -> Union[str, dict, Any]:
        try:
            data = await response.json(loads=self.json_loads, content_type=None)
        except ValueError:
            data = await response.text()

        return data

    async def process_response(self, response: ClientResponse) -> Union[str, dict, Any]:
        data = await self.response_to_native(response)

        if response.status != 200:
            await self.process_error(response, response.status, data)

        return data

    def get_error_message(self, response_data: Union[str, dict]) -> Union[str, dict]:
        if isinstance(response_data, dict) and "errors" in response_data:
            if (
                isinstance(response_data["errors"], dict)
                and "message" in response_data["errors"]
            ):
                return response_data["errors"]["message"]

        return response_data

    async def process_error(
        self, response: ClientResponse, code: int, response_data: Union[str, dict]
    ):
        message = self.get_error_message(response_data)
        raise ApiError(response, code, message)
