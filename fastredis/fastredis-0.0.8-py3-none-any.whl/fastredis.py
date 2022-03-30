#!/usr/bin/env python3
# coding = utf8
"""
@ Author : ZeroSeeker
@ e-mail : zeroseeker@foxmail.com
@ GitHub : https://github.com/ZeroSeeker
@ Gitee : https://gitee.com/ZeroSeeker
"""
import showlog
import redis
import envx


def make_con_info(
        env_file_name: str = 'redis.env'
):
    # ---------------- 固定设置 ----------------
    inner_env = envx.read(file_name=env_file_name)
    con_info = {
        "host": inner_env.get('host', 'localhost'),
        "port": int(inner_env.get('port', '6379')),
        "password": inner_env.get('password'),
        "max_connections": int(inner_env.get('max_connections', '10')),
    }
    # ---------------- 固定设置 ----------------
    return con_info


class Basics:
    def __init__(
            self,
            db=None,  # 需要连接的数据库
            con_info: dict = None,  # 连结信息，如果设置，将优先使用
            host=None,  # 连接的域名
            port=None,  # 连接的端口
            password=None,  # 连接的密码,
            max_connections=None
    ):
        # 初始化所有参数
        if db is None:
            self.con_db = 0
        else:
            self.con_db = db
        if con_info is not None:
            self.host = con_info.get('host')
            self.port = con_info.get('port')
            self.pwd = con_info.get('password')
            self.max_connections = con_info.get('max_connections')
            self.connection = self.connect()  # 执行连接
        else:
            self.host = host
            self.port = port
            self.pwd = password
            self.max_connections = max_connections
            self.connection = self.connect()  # 执行连接

    def connect(
            self
    ):
        # 执行连接
        pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.pwd,
            db=self.con_db,
            max_connections=self.max_connections
        )
        connection = redis.Redis(connection_pool=pool)
        return connection

    def get_db_key_list(
            self,
            connection=None
    ):
        """
        读取指定数据库的键列表
        """
        if connection is None:
            conn = self.connection
        else:
            conn = connection

        while True:
            try:
                keys = conn.keys()
                break
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

        key_list = list()
        for key in keys:
            key_list.append(key.decode())
        return key_list

    def read_list_key_values(
            self,
            key,
            connection=None
    ):
        """
        读取指定库的指定键的所有值列表
        """
        if connection is None:
            conn = self.connection
        else:
            conn = connection

        while True:
            try:
                values_count = conn.llen(key)  # 获取列表元素个数
                break
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

        values = list()
        for i in range(values_count):
            while True:
                try:
                    each_value = conn.lindex(key, i)
                    break
                except:
                    showlog.error('获取失败，准备重连')
                    self.connection = self.connect()
            if each_value is not None:
                values.append(each_value.decode())
        return values

    def list_add_l(
            self,
            key,
            value,
            connection=None
    ):
        # 在list左侧添加值
        if connection is None:
            conn = self.connection
        else:
            conn = connection

        while True:
            try:
                return conn.lpush(key, value)
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

    def list_add_r(
            self,
            key,
            value,
            connection=None
    ):
        # 在list右侧添加值
        if connection is None:
            conn = self.connection
        else:
            conn = connection

        while True:
            try:
                return conn.rpush(key, value)
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

    def list_pop_l(
            self,
            key,
            connection=None
    ):
        # 从左侧出队列
        if connection is None:
            conn = self.connection
        else:
            conn = connection

        while True:
            try:
                return conn.lpop(key)
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

    def list_pop_r(
            self,
            key,
            connection=None
    ):
        # 从右侧侧出队列
        if connection is None:
            conn = self.connection
        else:
            conn = connection

        while True:
            try:
                return conn.rpop(key)
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

    def set_string(
            self,
            name,
            value,
            connection=None,
            ex=None,
            px=None
    ):
        # 设置键值，ex过期时间（秒），px过期时间（毫秒）
        if connection is None:
            conn = self.connection
        else:
            conn = connection
        while True:
            try:
                return conn.set(
                    name,
                    value,
                    ex=ex,
                    px=px,
                    nx=False,
                    xx=False
                )
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

    def get_string(
            self,
            name,
            connection=None
    ):
        # 获取键值
        if connection is None:
            conn = self.connection
        else:
            conn = connection
        while True:
            try:
                return conn.get(name)
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()

    def delete_string(
            self,
            name,
            connection=None
    ):
        # 删除键值
        if connection is None:
            conn = self.connection
        else:
            conn = connection
        while True:
            try:
                return conn.delete(name)
            except:
                showlog.error('获取失败，准备重连')
                self.connection = self.connect()


def list_add_r(
        key,
        value,
        db: str = None,
        con_info: dict = None,  # 若指定，将优先使用
        env_file_name: str = 'redis.env'
):
    # ---------------- 固定设置 ----------------
    if con_info is None:
        con_info = make_con_info(env_file_name=env_file_name)
    else:
        pass
    if db is None:
        inner_db = db
    else:
        inner_db = None
    # ---------------- 固定设置 ----------------
    basics = Basics(
        db=inner_db,
        con_info=con_info
    )
    return basics.list_add_r(
        key=key,
        value=value
    )


def list_pop_l(
        key,
        db: str = None,
        con_info: dict = None,  # 若指定，将优先使用
        env_file_name: str = 'redis.env'
):
    # ---------------- 固定设置 ----------------
    if con_info is None:
        con_info = make_con_info(env_file_name=env_file_name)
    else:
        pass
    if db is None:
        inner_db = db
    else:
        inner_db = None
    # ---------------- 固定设置 ----------------
    basics = Basics(
        db=inner_db,
        con_info=con_info
    )
    return basics.list_pop_l(
        key=key
    )


def read_list_key_values(
        key,
        db: str = None,
        con_info: dict = None,  # 若指定，将优先使用
        env_file_name: str = 'redis.env'
):
    # ---------------- 固定设置 ----------------
    if con_info is None:
        con_info = make_con_info(env_file_name=env_file_name)
    else:
        pass
    if db is None:
        inner_db = db
    else:
        inner_db = None
    # ---------------- 固定设置 ----------------
    basics = Basics(
        db=inner_db,
        con_info=con_info
    )
    return basics.read_list_key_values(
        key=key
    )


def keys(
        db: str = None,
        con_info: dict = None,  # 若指定，将优先使用
        env_file_name: str = 'redis.env'
):
    """
    获取键列表
    """
    # ---------------- 固定设置 ----------------
    if con_info is None:
        con_info = make_con_info(env_file_name=env_file_name)
    else:
        pass
    if db is None:
        inner_db = db
    else:
        inner_db = None
    # ---------------- 固定设置 ----------------
    basics = Basics(
        db=inner_db,
        con_info=con_info
    )
    return basics.get_db_key_list()
