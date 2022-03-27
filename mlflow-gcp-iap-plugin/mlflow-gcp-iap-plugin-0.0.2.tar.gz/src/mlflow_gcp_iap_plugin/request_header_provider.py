from mlflow.tracking.request_header.abstract_request_header_provider import (
    RequestHeaderProvider,
)
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import os


class PluginRequestHeaderProvider(RequestHeaderProvider):
    """RequestHeaderProvider provided through plugin system"""

    def in_context(self):
        return True

    def request_headers(self):
        """Check if MLFLOW_IAP_CLIENT_ID has been set.  If so get id token and add to header."""
        headers = {}
        if os.environ.get("MLFLOW_IAP_CLIENT_ID"):
            client_id = os.environ.get("MLFLOW_IAP_CLIENT_ID")
            try:
                open_id_connect_token = id_token.fetch_id_token(Request(), client_id)
            except Exception as e:
                print(e)

            if open_id_connect_token:
                headers.update(
                    {"Authorization": "Bearer {}".format(open_id_connect_token)}
                )
        return headers
