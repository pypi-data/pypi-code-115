
import json
import time
import traceback
from datetime import date, datetime
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from .auth import get_token
from .contants import SOURCE, VERSION
from .enumlib.bigquery_schema_type_enum import BigquerySchemaType
from .env import is_debug


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, BigquerySchemaType):
            return obj._value_
        else:
            return json.JSONEncoder.default(self, obj)


def json_dumps(source):
    result = json.dumps(source, cls=ComplexEncoder)
    return result


def print_debug(*args, **kwargs):
    if is_debug():
        print(*args, **kwargs)
    return


def print_info(*args, **kwargs):
    print(*args, **kwargs)
    return


def api_request_with_token(url, method="POST", params=None, data=None):
    u_p = urlparse(url)
    query_dict = parse_qs(u_p.query)
    # 增加版本号
    query_dict['package_version'] = VERSION
    query_dict['source'] = SOURCE
    # scheme://netloc/path;parameters?query#fragment
    url = f"{u_p.scheme}://{u_p.netloc}{u_p.path}?{urlencode(query_dict)}#{u_p.fragment}"

    request_headers = {
        "Content-Type": "application/json",
        "authentication": get_token()
    }
    for i in range(3):
        try:
            print_debug(f"请求信息 url: {url}, params: {params}, headers: {request_headers}")
            if method == "GET":
                resp = requests.get(url, params=params, headers=request_headers, timeout=120)
            else:
                resp = requests.post(url, params=params, data=data, headers=request_headers, timeout=120)
            resp_text = resp.text
            print_debug(f"返回信息 {resp_text}")
            resp_json = resp.json()
            if resp_json['code'] == 0:
                return resp_json
            else:
                raise Exception(u"数据返回信息 %s" % resp_text)
        except Exception as e:
            print_debug(f"异常信息 {traceback.print_exc()}")
            print_info(e)
            time.sleep(2 ** (i+1))
    return {}
