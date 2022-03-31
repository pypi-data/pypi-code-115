
from .auth import request_login
from .contants import API_GET_TABLE_LIST_URL
from .utils import api_request_with_token, print_info


@request_login
def get_table_list():
    global TABLE_INFO_MAP
    resp_json = api_request_with_token(url=API_GET_TABLE_LIST_URL)
    if resp_json['code'] != 0:
        print_info("获取表异常")
        return

    return resp_json['data']
