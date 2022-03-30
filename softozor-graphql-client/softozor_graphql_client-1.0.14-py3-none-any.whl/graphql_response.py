from http.cookies import SimpleCookie
from typing import NamedTuple


class GraphQLResponse(NamedTuple):
    data: str
    cookies: SimpleCookie
    status_code: int
