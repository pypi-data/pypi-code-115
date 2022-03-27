import requests
import json


class Base:

    @classmethod
    def get_api(cls, get_url):
        print(get_url)
        get_data = requests.get(url=get_url)
        print(get_data.json())


class Send(Base):
    def __init__(self, url, token):
        self.get_url = None

        self.url = url
        self.token = token

    @staticmethod
    def str_make(args):
        cnum = 1
        url_string = ""

        for i in args:
            temp_string = 'c' + str(cnum)
            url_string += "&"+temp_string + "=" + i
            cnum += 1

        return url_string

    def send(self, f, *args):

        self.geturl=f"{self.url}?function={f}&token={self.token}{self.str_make(args)}"

        self.get_api(self.geturl)
        # "http://localhost:10002/MyQQAHTTPAPI?function=Api_OutPut&token=666&c1=123测试"


# bot = Send("http://localhost:8889/MyQQAHTTPAPI", "666")
# bot.send("Api_SendFriendMsg", "2696047693", '1420227537', 'test')
