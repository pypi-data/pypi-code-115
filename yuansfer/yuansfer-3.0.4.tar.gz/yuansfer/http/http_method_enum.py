# -*- coding: utf-8 -*-

class HttpMethodEnum(object):

    """Enumeration of an HTTP Method
    Attributes:
        GET: A GET Request
        POST: A POST Request
    """

    GET = "GET"

    POST = "POST"

    @classmethod
    def to_string(cls, val):
        """Returns the string equivalent for the Enum.
        """
        for k, v in list(vars(cls).items()):
            if v == val:
                return k

    @classmethod
    def from_string(cls, str):
        """Creates an instance of the Enum from a given string.
        """
        return getattr(cls, str.upper(), None)