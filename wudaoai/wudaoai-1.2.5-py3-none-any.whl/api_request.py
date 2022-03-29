# python3 -m pip install pycryptodome -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
# -*- coding:utf-8 -*-
import json
import time
from wudaoai.base_request import sendPost
from wudaoai.utils.rsa_util import rsa_encode

BASE_URL = "https://open.wudaoai.com/api/paas"

ENGINES_PATH = "/model/v1/open/engines/"

TOKEN_PATH = "/passApiToken/createApiToken"


def getToken(api_key, public_key):
    content = str(int(round(time.time() * 1000)))
    crypto = rsa_encode(content.encode("utf-8"), public_key)
    params = {"apiKey": api_key,
              "encrypted": crypto
              }
    data = sendPost(BASE_URL + TOKEN_PATH, params)
    data = json.loads(data)
    if data["code"] == 200:
        return data["data"]


def executeEngine(ability_type, engine_type, auth_token, params):
    req_engine_api_url = BASE_URL + ENGINES_PATH + ability_type + "/" + engine_type
    data = sendPost(req_engine_api_url, params, auth_token)
    data = json.loads(data)
    return data
