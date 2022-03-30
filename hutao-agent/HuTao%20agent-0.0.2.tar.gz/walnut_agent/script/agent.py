# -*- coding: utf-8 -*-

# @File    : agent.py
# @Date    : 2022-01-25
# @Author  : chenbo

"""
agent 客户端启动程序
"""

__author__ = 'chenbo'

import threading
from typing import List

from walnut_agent import ios_monkey
from walnut_agent.common import config
from walnut_agent.common.do_db import DataOp, dbname
from walnut_agent.script.app_handle import AppHandle, AdbHandle, TidHandle, tid
from walnut_agent.script.case_class import Platform, Feature
from walnut_agent.script.runner import Runner
from loguru import logger


# 通过任务id执行master下发的测试任务
def run_task(task_id: str) -> str:
    # 组装
    runner = Runner(task_id)
    runner.start()
    return runner.tag


# 获取设备号列表
def get_udid(platform: Platform) -> List[str]:
    udid = []
    app: AppHandle = None
    if platform == Platform.Android:
        app = AdbHandle()
    elif platform == platform.ios:
        app = TidHandle()
    # 重试3次
    for i in range(3):
        udid = app.get_devices()
        if len(udid) > 0:
            return udid
    return udid


def iOS_wda_start(udid: str) -> str:
    tid.switch_serial(udid)
    is_installed = tid.install_wda()
    if is_installed:
        return tid.start_wda(udid)
    else:
        return "WebDriverAgent start failed"


def iOS_monkey_start(udid, appid, target_time, throttle, yppno, tester):
    if tester == "":
        tester = 'huzhiming'
    with DataOp() as db:
        # 检测tester是否在表中
        result = db.fetchOne("SELECT username FROM {0}.auth_user WHERE username='{1}'".format(dbname, tester))
    if result == 0:
        return "该用户没有数据存档，请检查域账号的拼写。首次使用时，请先用该账号[{0}]登录一次tdp.yupaopao.com！"
    monkey = ios_monkey.SpiderMonkeyIOS(udid, appid)
    msg = "连接成功，正在运行monkey，请耐心等待"
    device_info = monkey.getDeviceInfo()
    phone_name = device_info["phone_name"]
    try:
        app_info = monkey.getAppInfo()
    except TypeError:
        msg = "[{0}]获取app信息失败，请检查是否安装了[{1}]".format(phone_name, monkey.app_name)
        logger.warning(msg)
    else:
        thr = threading.Thread(target=monkey.runMonkey,
                               args=(target_time, device_info, app_info, tester, yppno, throttle))
        thr.start()
    return msg


def iOS_monkey_shutdown(record_id):
    pass


def init_environment():
    """
    初始化环境
    """
    pass


if __name__ == '__main__':
    iOS_wda_start("679c48afa066538330baad04892da34b5264bf55")
