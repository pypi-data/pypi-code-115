
import random
import hashlib
import binascii
import os
import json
import re
from pymoran.timetool import TimeClass


class StrClass:
    def __init__(self) -> None:
        pass

    def random_num(self, length: int):
        '''
        创建纯数字随机字符串
        :param length 生成的字符串长度
        return {str} 生成的随机字符串
        '''
        result = ''
        pool = '0123456789'
        pool_len = len(pool)-1
        for i in range(length):
            result += pool[random.randint(0, pool_len)]
        return result

    def random_str(self, length: int):
        '''
        创建包含大小写字母和数字的随机字符串
        :param length 生成的字符串长度
        return {str} 生成的随机字符串
        '''
        result = ''
        pool = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        pool_len = len(pool)-1
        for i in range(length):
            result += pool[random.randint(0, pool_len)]
        return result

    def custom_random_str(self, pool: str, length: int):
        '''
        创建自定义范围的随机字符串
        :param pool 自定义字符串范围
        :param length 生成的字符串长度
        return {str} 生成的随机字符串
        '''
        result = ''
        pool_len = len(pool)-1
        for i in range(length):
            result += pool[random.randint(0, pool_len)]
        return result

    def hash_md5(self, enstr):
        """
        字符串md5加密
        :param enstr 需要加密的字符串
        return {str} 加密后的字符串
        """
        md = hashlib.md5()
        md.update(bytes(enstr, encoding='utf-8'))
        result = md.hexdigest()
        return result

    def hash_sha1(self, enstr):
        """
        字符串sha1加密
        :param enstr 需要加密的字符串
        return {str} 加密后的字符串
        """
        sha = hashlib.sha1()
        sha.update(bytes(enstr, encoding='utf-8'))
        result = sha.hexdigest()
        return result

    def password(self, pwd: str, salt: str):
        """
        根据原密码加盐获取新的加密密码
        :param pwd 原密码
        :param salt 盐值，盐值长度必须大于4
        return {str} 加密后的密码
        """
        salt1 = salt[0:4]
        salt2 = salt[4:]
        pwd = salt1+pwd+salt2
        return self.hash_md5(pwd)

    def access_token(self, uniqueid: str):
        """
        生成唯一access_token
        :param pwdStr 原密码
        :param salt 盐值，盐值长度必须大于4
        """
        timeclass = TimeClass()
        result = str(uniqueid)+str(timeclass.timestamp())
        result = self.hash_md5(result)
        result = result + str(binascii.b2a_base64(os.urandom(108))[:-1])
        result = result.replace('\'', '')
        result = result.replace('/', '')
        return result

    # def symbol_replace(self,val):
    #     '''
    #     替换文本中的特殊字符
    #     :param val {str} 需要替换的字符串
    #     :return {str} 替换后的字符串
    #     '''
    #     val=val.replace('\'','&#39;')
    #     val=val.replace('´','&#180;')
    #     val=val.replace('`','&#96;')
    #     return val

class JsonClass:
    def __init__(self):
        pass

    def jsonToDumps(self, data:dict):
        '''
        将字典类型数据转换成str
        :param data 字典类型数据
        :return {str} 转换后的json格式字符串
        '''
        return json.dumps(data)

    def jsonToLoads(self, jsonstr:str):
        '''
        将json字符串数据转换成字典类型
        :param jsonstr json字符串
        :return {dict} 转换后的dict数据
        '''
        if jsonstr == None:
            return jsonstr
        elif type(jsonstr) == bytes:
            jsonstr = jsonstr.decode()
        return json.loads(jsonstr)

    # def jsonQuerySetToDumps(self, data):
    #     '''
    #     转换QuerySet类型数据并输出json格式字符串
    #     :param data {QuerySet} QuerySet/list数据
    #     :return {str} 转换后的json格式字符串
    #     '''
    #     if type(data) != list:
    #         data = list(data)
    #     result = json.dumps(data, ensure_ascii=False, cls=DjangoJSONEncoder)
    #     return result

    # def jsonQuerySetToLoads(self, data):
    #     '''
    #     转换QuerySet类型数据并输出dict

    #     @param data {QuerySet} QuerySet/list数据

    #     return {dict} 转换后的dict数据
    #     '''
    #     result = self.jsonQuerySetToDumps(data)
    #     result = json.loads(result)
    #     return result

class RegularClass:
    def __init__(self):
        pass

    def pInt(self, value:str, include_zero:bool=True):
        '''
        正整数
        :param value 需要验证的字符串
        :param include_zero 是否包含0，默认True，包含
        :return {bool} 验证结果，True/False
        '''
        value = str(value)
        result = ''
        if include_zero:
            result = re.match(r'^[0-9]+$', value)
        else:
            result = re.match(r'^[1-9]\d*$', value)
        print(result)
        if result:
            return True
        return False

    def check_num(self, val):
        '''
        验证0和正整数
        '''
        val = str(val)
        result = re.match(r'^\d+$', val)
        if result:
            return True
        return False

    def check_price(self, val):
        result = re.match(r'^[0-9]+(.[0-9]{2})?$', val)
        if result:
            return True
        return False

    def check_username(self, username):
        result = re.match(r'^[a-zA-Z0-9_-]{4,20}$', username)
        if result:
            return True
        return False

    def check_phone(self, phone):
        result = re.match(r'^1[3456789]\d{9}$', phone)
        if result:
            return True
        return False

    def check_password(self, password):
        result = re.match(r'^[\w!@#$%^&*.]{6,20}$', password)
        if result:
            return True
        return False

    def check_ipv4(self, ip):
        result = re.match(
            r'^(((\d{1,2})|(1\d{2})|(2[0-4]\d)|(25[0-5]))\.){3}((\d{1,2})|(1\d{2})|(2[0-4]\d)|(25[0-5]))$',
            ip
        )
        if result:
            return True
        return False

    def email(self, val):
        result = re.match(
            r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', val)
        if result:
            return True
        return False


if __name__ == '__main__':
    regular=RegularClass()
    regular.pInt(123)
