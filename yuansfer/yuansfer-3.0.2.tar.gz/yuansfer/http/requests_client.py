# -*- coding: utf-8 -*-
import json
from requests.sessions import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from yuansfer.http.http_client import HttpClient
from yuansfer.http.http_method_enum import HttpMethodEnum
from yuansfer.http.http_response import HttpResponse

class RequestsClient(HttpClient):

    """An implementation of HttpClient that uses Requests as its HTTP Client
    Attributes:
        timeout (int): The default timeout for all API requests.
    """

    def __init__(self,
                 timeout=60,
                 cache=False,
                 max_retries=None,
                 verify=True):
        """The constructor.
        Args:
            timeout (float): The default global timeout(seconds).
        """
        self.timeout = timeout
        self.session = Session()

        retries = Retry(total=max_retries)
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        self.session.verify = verify

    def execute(self, request):
        """Execute a given HttpRequest to get a string response back
        Args:
            request (HttpRequest): The given HttpRequest to execute.
        Returns:
            HttpResponse: The response of the HttpRequest.
        """
        response = self.session.request(
            HttpMethodEnum.to_string(request.http_method),
            request.query_url,
            headers=request.headers,
            params=request.query_parameters,
            data=json.dumps(request.parameters),
            timeout=self.timeout
        )

        return self.convert_response(response, request)

    def convert_response(self, response, http_request):
        """Converts the Response object of the HttpClient into an
        HttpResponse object.
        Args:
            response (dynamic): The original response object.
            http_request (HttpRequest): The original HttpRequest object.
        Returns:
            HttpResponse: The converted HttpResponse object.
        """
        return HttpResponse(
                response.status_code,
                response.text,
                response.headers,
                http_request
            )