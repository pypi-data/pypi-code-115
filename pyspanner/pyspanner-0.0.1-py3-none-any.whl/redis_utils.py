# -*- encoding: utf-8 -*-
# @Author: haohongcheng
# @Date:
# @Description:
from typing import List, Tuple, Optional

from redis.client import Redis
from redis.cluster import RedisCluster
from redis.sentinel import Sentinel

REDIS_MODE_DIRECT = "direct"
REDIS_MODE_UNIXSOCKET = "unixsocket"
REDIS_MODE_SENTINEL = "sentinel"
REDIS_MODE_CLUSTER = "cluster"
REDIS_MODES = [REDIS_MODE_DIRECT, REDIS_MODE_UNIXSOCKET, REDIS_MODE_SENTINEL, REDIS_MODE_CLUSTER]


class RedisUtil:
    def __init__(self,
                 mode: str = REDIS_MODE_DIRECT,
                 host: str = "localhost", port: int = 6379,
                 unixpath: str = None,
                 sentinel_list: List[Tuple] = None, master_name: str = None,
                 db: int = 0,
                 passwd: str = None,
                 decode_responses: bool = True,
                 ssl: bool = True, ssl_ca_certs: str = None,
                 health_check_interval: int = 60,
                 timeout: int = 30):
        self.host = host
        self.port = port
        self.unixpath = unixpath
        self.sentinel_list = sentinel_list
        self.master_name = master_name
        self.db = db
        self.passwd = passwd
        self.decode_resp = decode_responses
        self.ssl = ssl
        self.ssl_ca_certs = ssl_ca_certs
        self.health_check_interval = health_check_interval
        self.timeout = timeout
        self.mode = mode.lower()
        if self.mode not in REDIS_MODES:
            raise ValueError

        self.sentinel: Optional[Sentinel] = None
        self.rc: Optional[Redis | RedisCluster] = None
        if self.mode == REDIS_MODE_DIRECT:
            # 直连
            if not isinstance(self.host, str):
                raise TypeError("直连模式必须指定端口 host (类型: str)")
            if not isinstance(port, int):
                raise TypeError("直连模式必须指定端口 port (类型: int)")
            self.rc = Redis(host=self.host, port=self.port,
                            db=self.db,
                            password=self.passwd,
                            socket_timeout=self.timeout,
                            socket_connect_timeout=self.timeout,
                            socket_keepalive=True,
                            encoding="utf-8",
                            decode_responses=self.decode_resp,
                            ssl=self.ssl, ssl_ca_certs=self.ssl_ca_certs,
                            health_check_interval=self.health_check_interval)
        if self.mode == REDIS_MODE_UNIXSOCKET:
            # 本机
            if not isinstance(self.unixpath, str):
                raise TypeError("本机模式必须指定路径 unixpath (类型: str)")
            self.rc = Redis(unix_socket_path=self.host,
                            db=self.db,
                            password=self.passwd,
                            socket_timeout=self.timeout,
                            socket_connect_timeout=self.timeout,
                            socket_keepalive=True,
                            encoding="utf-8",
                            decode_responses=self.decode_resp,
                            ssl=self.ssl, ssl_ca_certs=self.ssl_ca_certs,
                            health_check_interval=self.health_check_interval)
        if self.mode == REDIS_MODE_SENTINEL:
            # 哨兵
            self.sentinel = Sentinel(self.sentinel_list,
                                     password=self.passwd,
                                     socket_timeout=self.timeout,
                                     socket_connect_timeout=self.timeout,
                                     socket_keepalive=True,
                                     encoding="utf-8",
                                     decode_responses=self.decode_resp,
                                     ssl=self.ssl, ssl_ca_certs=self.ssl_ca_certs,
                                     health_check_interval=self.health_check_interval)
            # noinspection PyNoneFunctionAssignment
            self.rc = self.sentinel.master_for(self.master_name, redis_class=Redis)
        if self.mode == REDIS_MODE_CLUSTER:
            # 集群
            self.rc = RedisCluster(host=self.host, port=self.port, db=self.db,
                                   password=self.passwd,
                                   socket_timeout=self.timeout,
                                   socket_connect_timeout=self.timeout,
                                   socket_keepalive=True,
                                   encoding="utf-8",
                                   decode_responses=self.decode_resp,
                                   ssl=self.ssl, ssl_ca_certs=self.ssl_ca_certs,
                                   health_check_interval=self.health_check_interval)

    def update_master(self):
        if self.mode == REDIS_MODE_SENTINEL and isinstance(self.sentinel, Sentinel):
            # noinspection PyNoneFunctionAssignment
            self.rc = self.sentinel.master_for(self.master_name, redis_class=Redis)

    def get_connection(self) -> Optional[Redis | RedisCluster]:
        return self.rc


if __name__ == "__main__":
    pass
