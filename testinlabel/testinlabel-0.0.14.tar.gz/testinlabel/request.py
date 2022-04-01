from . import *
import requests
import json
import hashlib
import time


class Request:
    def __init__(self, host, AK, task_key, debug=False):
        self.__TASK_URL = f'{host}open/v1/taskinfo/{task_key}/get-label-data'
        self.__AK = AK
        self.__DEBUG = debug

    def __getTaskInfo(self, key, has_unable, statuss):
        page = 1
        taskList = []
        res = {}
        status = statuss[0]

        hasUnable = 0
        if has_unable: hasUnable = 1

        while status in statuss:
            data = {
                "page": page,
                "page_num": 20,
                "has_unable": hasUnable,
                "status": status,
            }
            headers = {'Content-Type': 'application/json', 'Access-Key': self.__AK}
            page += 1
            r = requests.get(self.__TASK_URL, params=data, headers=headers)
            res = r.json()
            if self.__DEBUG and res['data'] != {}:
                print(
                    f"[DOWNLOAD_LABEL_DATA] download labeled data from server, taskName:{res['data']['task_name']}, status:{status}, taskTotal:{res['data']['total']}, current Page:{res['data']['page']}, per page items:{res['data']['page_num']}"
                )
            if not res['data'] or not res['data']['task_list']:
                log_info = r.json()
                log_info['key'] = key
                log_info['status'] = status
                status += 1
                page = 1
                continue
            taskList += res['data']['task_list']
        if res: res['data']['task_list'] = taskList
        return res

    def getTaskData(self, key, hasUnable=False, status=[STATUS_PASS, STATUS_CHECK_WAIT, STATUS_INSPECTOR_WAIT]):
        markDatas = self.__getTaskInfo(key=key, has_unable=hasUnable, statuss=status)
        return markDatas