"""Main module."""
import pandas as pd
import requests


class TiingoNewsAPI:

    def __init__(self, token: str = None, ):
        self.token = token
        self.api_base_endpoint = "https://api.tiingo.com/tiingo"
        self.headers = {
            'Content-Type': 'application/json'
        }

    def get_news_data(self):
        data_endpoint = f"{self.api_base_endpoint}/news"
        data = pd.DataFrame(requests.get(data_endpoint, headers=self.headers, params=self.payload).json())
        return data
