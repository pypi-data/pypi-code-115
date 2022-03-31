# coding: utf8

__all__ = ["RequestMethod", "EndpointData"]

import collections
from enum import Enum, unique

Error = collections.namedtuple("Error", ["code", "message"])


@unique
class RequestMethod(Enum):
    """
    The RESTful Data service can support multiple methods when
    sending requests to a specified endpoint.
       GET : Request data from the specified endpoint.
       POST : Send data to the specified endpoint to create/update a resource.
       DELETE : Request to delete a resource from a specified endpoint.
       PUT : Send data to the specified endpoint to create/update a resource.
    """

    GET = 1
    POST = 2
    DELETE = 3
    PUT = 4


class EndpointData(object):
    def __init__(self, raw, dataframe=None):
        if raw is None:
            raw = {}
        self._raw = raw
        self._dataframe = dataframe

    @property
    def raw(self):
        return self._raw

    @property
    def df(self):
        return self._dataframe
