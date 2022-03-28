# -*- coding: utf-8 -*-
import http.client
from urllib.parse import urlparse

class Discord_msg():
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.domain = urlparse(self.webhook_url).netloc

    def send(self, msg):
        formdata = "------:::BOUNDARY:::\r\nContent-Disposition: form-data; name=\"content\"\r\n\r\n" + msg + "\r\n------:::BOUNDARY:::--"

        connection = http.client.HTTPSConnection(self.domain)
        connection.request("POST", self.webhook_url, formdata.encode('utf-8'), {
            'content-type': "multipart/form-data; boundary=----:::BOUNDARY:::",
            'cache-control': "no-cache"
            })
        response = connection.getresponse()
        result = response.read()
        return(result.decode("utf-8"))

if __name__ == '__main__':
    pass