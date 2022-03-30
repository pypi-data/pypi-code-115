# -*- coding: UTF-8 -*-
import ctypes
import threading
import traceback

from tidevice import Usbmux, Device, exceptions

from walnut_agent.common.do_db import DataOp, dbname
from loguru import logger
from walnut_agent.common import config, do_monkeylog, mail
import time

from walnut_agent.script.app_handle import process_cmd
from walnut_agent.script.util_handle import setting


def getDevices():
    """ios 获取已连接的设备id及其连接状态"""
    devices = {}
    for info in Usbmux().device_list():
        devices[info.udid] = info.conn_type
    return devices


def getDevice(udid):
    try:
        getDevices()[udid]
    except KeyError as e:
        logger.warning("没有检测到设备，请检查USB连接是否正常！")
        raise e
    else:
        logger.info("已获取设备id:" + udid + '\r\n')
        return Device()


def stopMonkey(record_id, tid):
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(int(tid)), ctypes.py_object(SystemExit))
    with DataOp() as db:
        sql = "SELECT appid, udid, phone_name, begin_time,phone_brand,phone_type,phone_sys,version_name,version_code,tester,run_status FROM " \
              "{0}.test_record_ios WHERE record_id={1}".format(dbname, record_id)
        result = db.fetchOne(sql)
        phone_name = result["phone_name"]
        if res == 0:
            msg = "设备[{0}]终止测试失败，线程id错误！".format(phone_name)
            kv = {"run_status": 6}
        elif res != 1:
            # "if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            msg = "设备[{0}]终止测试失败，线程状态设置失败！".format(phone_name)
            kv = {"run_status": 6}
        else:
            msg = "设备[{0}]终止测试成功！".format(phone_name)
            kv = {"run_status": 2}
        db.update("test_record_ios", kv, "record_id={0}".format(record_id))
    return msg


class _caffeinateThread(threading.Thread):
    def __init__(self, duration: int):
        super().__init__()
        self.duration = duration

    def run(self) -> None:
        process_cmd("caffeinate -t " + self.duration)


class SpiderMonkeyIOS:
    def __init__(self, udid=None, appid=1):
        self.appid = int(appid)
        self.udid = udid
        self._monkey_t: threading.Thread = None
        self.device = getDevice(udid)
        # 给定初始机器名，防止获取机器名失败
        self.phone_name = udid
        with DataOp() as db:
            result = db.fetchAll("SELECT app_name, bundle_id FROM {0}.app_info WHERE appid={1};".format(dbname, appid))[
                0]
            self.bundle_id = result["bundle_id"]
            self.app_name = result["app_name"]

    def install_runner(self):
        app_list = self.device.installation.iter_installed()
        for app in app_list:
            if app['CFBundleIdentifier'] == config.fast_bundle_id:
                logger.info("设备[{0}]已安装过[{1}]".format(self.phone_name, config.fast_bundle_id))
                return 1
        try:
            self.device.app_install(setting.app.runner_path.__str__())
        except exceptions.ServiceError:
            logger.error("应用认证异常，安装失败！")
            return 0
        else:
            return 1

    def getDeviceInfo(self):
        device_info = self.device.device_info()
        # market_name转换为机型名称
        try:
            model = config.iphone_model[device_info["ProductType"]]
        except KeyError as e:
            model = None
            logger.warning("设备[{0}]marketName[{1}]无法解析!".format(self.phone_name, device_info["ProductType"]))
        self.phone_name = device_info["DeviceName"]
        return {"phone_name": self.phone_name, "phone_sys": device_info["ProductVersion"],
                "phone_type": model, "phone_brand": "Iphone"}

    def getAppInfo(self):
        app_info = self.device.installation.lookup(self.bundle_id)
        return {"version_name": app_info["CFBundleShortVersionString"], "version_code": app_info["CFBundleVersion"]}

    def runMonkey(self, target_time, product_info, app_info, tester, yppno, throttle=300, count=10):
        import threading
        tid = threading.get_ident()
        target_time = int(target_time)
        subTime, runTime = 0, 0
        testTime = target_time
        situation = []
        version_name = app_info["version_name"]
        version_code = app_info["version_code"]
        phone_brand = product_info["phone_brand"]
        phone_type = product_info["phone_type"]
        phone_sys = product_info["phone_sys"]
        begin_time = time.strftime("%Y-%m-%d %H:%M:%S")
        values = (self.appid, version_name, version_code, begin_time, phone_brand, phone_type, phone_sys, target_time,
                  tester, self.udid, 0, 0, tid, "[]", self.phone_name, yppno)
        with DataOp() as db:
            db.insert("test_record_ios", config.test_record_cols_before, values)
            record_id = db.fetchOne("SELECT LAST_INSERT_ID();")['LAST_INSERT_ID()']
        i = 0
        # 防报错，给定初始值
        ANR_count = 0
        crash_count = 0
        bug_numbers = []
        end_time = ""
        import math
        try:
            # 运行monkey并进行时间补偿
            while i < count:
                with DataOp() as db:
                    kv = {"run_status": 0, "duration": sum(situation)}
                    db.update("test_record_ios", kv, "record_id={0}".format(record_id))
                curTime = time.time()
                self.device.xctest(config.fast_bundle_id, env={"BUNDLEID": self.bundle_id, "duration": target_time,
                                                               "throttle": throttle})
                runTime = math.floor((time.time() - curTime) / 60)
                # 运行时间小于1分钟时，视为连接失败，失败次数+1并且进行重试
                if runTime < 1:
                    logger.error("设备[{0}]运行时间小于1分钟！".format(self.phone_name))
                situation.append(runTime)
                subTime = testTime - runTime
                testTime = subTime
                end_time = time.strftime("%Y-%m-%d %H:%M:%S")
                # 预期时间与实际时间的相差值小于等于1时跳出循环
                if subTime <= 1:
                    run_status = 1
                    break
                else:
                    logger.info("设备[{0}]运行时间低于预期时间，5分钟后开始时间补偿！".format(self.phone_name))
                    time.sleep(300)
                    run_status = 3
                    # 补偿前及时更新end_time和run_status
                    kv = {"end_time": end_time, "run_status": run_status}
                    with DataOp() as db:
                        db.update("test_record_ios", kv, "record_id={0}".format(record_id))
        except BaseException as e:
            if isinstance(e, SystemExit):
                run_status = 2
            else:
                logger.error("设备[{0}]运行异常！异常信息:\n{1}".format(self.phone_name, traceback.format_exc()))
                run_status = -1
            # 防止运行异常时不能正确写入end_time和duration
            runTime = int((time.time() - curTime) / 60)
            situation.append(runTime)
            end_time = time.strftime("%Y-%m-%d %H:%M:%S")
            raise e
        else:
            # 次数用尽之后仍然没有重连成功
            if subTime <= 1 and i >= count:
                logger.info("设备[{0}]连接失败次数{1}用尽，结束运行！".format(self.phone_name, count))
                run_status = 4
        len_situation = len(situation)
        duration = sum(situation)
        logger.info("设备[{0}]本次目标运行时间为{1}分钟,实际运行时间{2}分钟".format(self.phone_name, target_time, duration))
        for i_success in range(len_situation):
            logger.info("设备[{0}]第{1}次运行了{2}分钟".format(self.phone_name, i_success + 1, situation[i_success]))
        coverage_mail = "IOS暂不支持获取事件覆盖率"
        mail_content = "测试人员：{0}\r预期运行时长：{1}分钟\r实际运行时长：{2}分钟\r运行状态：{3}\r运行时间：{4} - {5}\r事件覆盖率：" \
                       "{6}\r\r设备信息：\r设备名称：{7}\r手机型号：{8} {9}\r系统版本：{10}\r\rapp信息：\r版本号：{11}\rbuild_id：" \
                       "{12}".format(tester, target_time, duration, config.run_status[run_status], begin_time,
                                     end_time, coverage_mail, self.phone_name, phone_brand, phone_type, phone_sys,
                                     version_name,
                                     version_code)
        # 运行失败、成功、手动终止时自动收集并上报log
        if run_status in [-1, 1, 2]:
            JiraOp = do_monkeylog.JiraOp(self.appid, domain="mat")
            # [a:b,c:d]
            bug_infos = JiraOp.collectLog(yppno=yppno, begin_time=begin_time, end_time=end_time)
            bug_infos = JiraOp.bugDistinct(bug_infos, version_name)
            for i in range(bug_infos[2]):
                report_info = JiraOp.logReport(bug_infos[0][i], bug_infos[1][i], version_name, tester)
                if isinstance(report_info, tuple):
                    ANR_count = report_info[0]
                    crash_count = report_info[1]
                    bug_numbers = report_info[2]
                    if len(bug_numbers) > 0:
                        bug_urls = ["http://jira.yupaopao.com/browse/" + bug_number for bug_number in bug_numbers]
                        mail_content += "\r\rANR次数：{0}\rcrash次数：{1}\rbug列表：\r{2}".format(ANR_count, crash_count,
                                                                                         do_monkeylog.listToStr(
                                                                                             bug_urls). replace(",",
                                                                                                                "\r"))
                    else:
                        mail_content += "\r\rANR次数：{0}\rcrash次数：{1}".format(ANR_count, crash_count)
                    # 掐头去尾，用于存入数据库
                    bug_numbers = do_monkeylog.listToStr(bug_numbers)
                else:
                    msg = "设备[{0}]提交BUG失败！{1}".format(self.phone_name, report_info)
                    run_status = 7
                    logger.error(msg)
                    mail_content += "\r\r{0}".format(msg)
        else:
            logger.error("设备[{0}]运行状态流转异常，当前状态{1}！".format(self.phone_name, run_status))
        # 同步测试记录到db
        kv = {"duration": duration, "end_time": end_time, "ANR_count": ANR_count, "crash_count": crash_count,
              "bug_number": bug_numbers, "run_status": run_status}
        with DataOp() as db:
            db.update("test_record_ios", kv, "record_id={0}".format(record_id))
        # 发送测试报告邮件
        mail.Mail().sendMail(mail_content, tester.split(","))


if __name__ == '__main__':
    pass
