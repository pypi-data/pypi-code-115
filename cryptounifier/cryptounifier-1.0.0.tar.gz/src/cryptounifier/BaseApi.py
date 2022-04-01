#!/usr/bin/env python
import json
import requests


class BaseApi(object):

    def __init__(self, suffix, headers):

        self.defaultUrl = "https://cryptounifier.io/api/v1/"
        self.suffix = suffix
        self.headers = headers
        self.baseUrl = self.defaultUrl+self.suffix

    def setApiUrl(self, url):
        self.defaultUrl = url
        self.baseUrl = self.defaultUrl+self.suffix

    def prepareRequest(self, requestDict):
        resultDict = {}
        for key, value in requestDict.items():
            if value != None:
                 resultDict[key] = value
        return resultDict
        
    def executeRequest(self, method, uri, body={}):
        if body != None:
            body = self.prepareRequest(body)
        if method == 'POST':
            return requests.post(self.baseUrl+'/'+uri, headers=self.headers, data=json.dumps(body)).content
        else:
            return requests.get(self.baseUrl+'/'+uri, headers=self.headers).content
