from http.cookies import SimpleCookie
from typing import NamedTuple


class GraphQLResponse(NamedTuple):
    payload: dict
    cookies: SimpleCookie
    status_code: int
