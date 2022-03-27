from typing import Union

from aiohttp import ClientResponse


class ApiError(Exception):
    def __init__(self, response: ClientResponse, code: int, message: Union[str, dict]):
        self.code = code
        self.message = message
        self.response = response

    def __repr__(self):
        return f"{self.__class__.__name__}: code={self.code}, message={self.message}"

    def __str__(self):
        return (
            f"{self.__class__.__name__}: "
            f"code={self.code}, "
            f"message={self.message}, "
            f"url={self.response.url}, "
            f"headers={self.response.headers}"
        )
