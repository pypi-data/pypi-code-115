from os import environ
from urllib.parse import urlsplit

__all__ = ("docker_host",)


def docker_host() -> str:
    host = environ.get("DOCKER_HOST", "")
    res = urlsplit(host)
    return res.hostname if res.hostname else "localhost"
