# -*- coding: utf-8 -*-
class ApiResponse:

    """Http response received.
    Attributes:
        status_code (int): The status code response from the server that
            corresponds to this response.
        response (string): The reason phrase returned by the server.
        request (HttpRequest): The request that resulted in this response.
        body (Object): The data field specified for the response
        errors (object): Any errors returned by the server
    """

    def __init__(self, http_response,
                 body=None,
                 errors=None):

        """The Constructor
        Args:
            http_response (HttpResponse): The original, raw response from the api
            data (Object): The data field specified for the response
            errors (object): Any errors returned by the server
        """

        self.status_code = http_response.status_code
        self.response = http_response.response
        self.request = http_response.request
        self.body = body
        self.errors = errors

    def is_success(self):
        """ Returns true if status code is between 200-300
        """
        return 200 <= self.status_code < 300

    def is_error(self):
        """ Returns true if status code is between 400-600
        """
        return 400 <= self.status_code < 600

    def __repr__(self):
        return '<ApiResponse [%s]>' % (self.response)