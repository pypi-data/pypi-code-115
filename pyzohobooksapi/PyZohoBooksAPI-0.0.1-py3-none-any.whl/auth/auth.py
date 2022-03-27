from PyZohoBooksAPI.api import API


class ZohoAuth(API):
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def generate_token(self, code):
        url = 'https://accounts.zoho.com/oauth/v2/token'
        headers = {}
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": "https://www.example.com/return/",
            "code": code,
            }
        result = self._start_connection(method='POST', url=url, headers=headers, params=params)
        return self._parse_response(result)
        # return result

    def refresh_token(self, refresh_token):
        url = 'https://accounts.zoho.com/oauth/v2/token'
        headers = {}
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            # "redirect_uri": "https://www.example.com/return/",
            "refresh_token": refresh_token,
            }
        result = self._start_connection(method='POST', url=url, headers=headers, params=params)
        return self._parse_response(result)
