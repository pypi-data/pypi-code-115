import requests

class Beacon:
    def __init__(self, api_key=None, debug=False) -> None:
        self.api_key = api_key
        self.url = (
            "http://localhost:8000/api/ping/"
            if debug
            else "https://server-chat-backend.herokuapp.com/api/ping/"
        )
        pass

    def send(self, data=None) -> None:

        if self.api_key is None:
            raise Exception("No API key provided")

        message = data.get("message")
        channel = data.get("channel")

        if message is None:
            raise Exception("No message provided")

        if channel is None:
            raise Exception("No channel provided")

        headers = {"Beacon-Key": self.api_key}

        return requests.post(
            url=self.url, headers=headers, data={"body": message, "channel": channel}
        )

