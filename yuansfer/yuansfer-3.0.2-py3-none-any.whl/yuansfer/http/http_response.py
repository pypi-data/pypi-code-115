# -*- coding: utf-8 -*-
import json

class HttpResponse(object):

    """Information about an HTTP Response including its status code, returned
        headers, and raw body
    Attributes:
        status_code (int): The status code response from the server that
            corresponds to this response.
        response (json): The reason phrase returned by the server.
        headers (dict): A dictionary of headers (key : value) that were
            returned with the response
        request (HttpRequest): The request that resulted in this response.
    """

    def __init__(self,
                 status_code,
                 response,
                 headers,
                 request):
        """Constructor for the HttpResponse class
        Args:
            status_code (int): The response status code.
            response (json): The response reason phrase.
            headers (dict): The response headers.
            request (HttpRequest): The request that resulted in this response.
        """
        self.status_code = status_code
        self.response = json.loads(response)
        self.headers = headers
        self.request = request