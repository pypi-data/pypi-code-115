# -*- coding: utf-8 -*-
from yuansfer.http.requests_client import RequestsClient

class Configuration(object):
    """ User to input their configuration value
    """

    @property
    def http_client(self):
        return self._http_client

    @property
    def timeout(self):
        return self._timeout

    @property
    def max_retries(self):
        return self._max_retries

    @property
    def merchantNo(self):
        return self._merchantNo

    @property
    def storeNo(self):
        return self._storeNo

    @property
    def token(self):
        return self._token

    @property
    def environment(self):
        return self._environment

    def __init__(self, timeout=60, max_retries=3, environment='production', merchantNo=None, storeNo=None, token=None):

        # The value to use for connection timeout
        self._timeout = timeout

        # The number of times to retry an endpoint call if it fails
        self._max_retries = max_retries

        # Current API environment
        self._environment = environment

        self._merchantNo = merchantNo

        self._storeNo = storeNo

        self._token = token

        # The Http Client to use for making requests.
        self._http_client = self.create_http_client()

    def create_http_client(self):
        return RequestsClient(timeout=self.timeout,
                              max_retries=self.max_retries)

    # All environments
    environments = {
        'production': 'https://mapi.yuansfer.com',
        'sandbox': 'https://mapi.yuansfer.yunkeguan.com'
    }

    def get_base_uri(self):
        """Generates the appropriate base URI for the environment and the
        server.
        Args:
            server (Configuration.Server): The server enum for which the base
            URI is required.
        Returns:
            String: The base URI.
        """
        return self.environments[self.environment]
