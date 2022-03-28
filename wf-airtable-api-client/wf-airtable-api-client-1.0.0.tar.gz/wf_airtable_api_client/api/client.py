import json
import requests

from wf_airtable_api_schema.models.hubs import ListAPIHubResponse
from .. import const


class Api:
    def __init__(self,
                 audience: str = const.WF_AIRTABLE_API_AUTH0_AUDIENCE,
                 auth_domain: str = const.WF_AIRTABLE_API_AUTH0_DOMAIN,
                 client_id: str = const.WF_AIRTABLE_API_AUTH0_CLIENT_ID,
                 client_secret: str = const.WF_AIRTABLE_API_AUTH0_CLIENT_SECRET,
                 api_url: str = const.WF_AIRTABLE_API_URL):
        self.audience = audience
        self.auth_domain = auth_domain
        self.auth_url = f"https://{self.auth_domain}"

        self.client_id = client_id
        self.client_secret = client_secret

        self.access_token = self.load_token()

        self.api_url = api_url

    def load_token(self,):
        response = requests.post(
            url=f"{self.auth_url}/oauth/token",
            data=json.dumps({
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": self.audience,
                "grant_type": "client_credentials"}),
            headers={"content-type": "application/json"})

        data = response.json()
        return data['access_token']

    def fetch(self, path):
        response = requests.get(
            url=f"{self.api_url}/{path}",
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {self.access_token}"
            }
        )
        return response.json()

    def list_hubs(self):
        h = self.fetch("hubs")
        response = ListAPIHubResponse.parse_obj(h)
        print(response.data)
