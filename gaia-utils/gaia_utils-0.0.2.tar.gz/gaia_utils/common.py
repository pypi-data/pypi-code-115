
import json
import sys
from datetime import date

from pandas import DataFrame

from .auth import request_login
from .bigquery_utils import query_bigquery
from .contants import API_UPLOAD_DATA_SIZE_LIMIT, API_UPLOAD_URL
from .enumlib.load_data_frame_type_enum import LoadDataframeType
from .env import is_debug
from .utils import api_request_with_token, json_dumps, print_debug, print_info


@request_login
def load_dataframe(_type: LoadDataframeType, content: str) -> DataFrame:
    result = None
    sql = ""
    if _type == LoadDataframeType.SQL:
        sql = content
    elif _type == LoadDataframeType.TABLE:
        print_info("暂不开放")
        return
    if sql:
        result = query_bigquery(sql)
    return result


@request_login
def submit(project_id: str, dataset_id: str, table_name: str,
           pd_data: DataFrame, table_field_schema: list = None, table_date: date = None,
           update_force: bool = False, reset_force: bool = False) -> bool:
    # 检查 pd_data 限制上传，提醒
    size_m = round((sys.getsizeof(pd_data) / 1024 / 1024), 2)
    if size_m > API_UPLOAD_DATA_SIZE_LIMIT:
        print_info(f"pd_data({size_m}) MB 大于 {API_UPLOAD_DATA_SIZE_LIMIT} MB 限制上传")
        return False

    json_config = {
        "orient": 'records',
        "date_format": 'iso'
    }
    if is_debug():
        json_config['indent'] = 4
    pd_data_json_str = pd_data.to_json(**json_config)
    # pd_data_json_str = pd_data.to_json(orient='records', indent=4, date_unit='s')
    print_debug("pd_data_json_str", pd_data_json_str)
    req_data = {
        "tableName": table_name,
        "tableData": json.loads(pd_data_json_str),
        "tableDate": table_date,
        "projectId": project_id,
        "datasetId": dataset_id,
        "updateForce": update_force,
        "resetForce": reset_force,
        "tableFieldSchema": table_field_schema,
    }
    data = json_dumps(req_data)
    print_debug("data", data)
    resp_json = api_request_with_token(url=API_UPLOAD_URL, data=data)
    if resp_json['code'] == 0:
        print_info("上传成功")
        return True
    else:
        print_info("上传失败")
    return False


@request_login
def save_csv(filename: str, pd_data: DataFrame):
    pd_data.to_csv(filename, index=False, date_format='%Y-%m-%d %H:%M:%S')
    return
