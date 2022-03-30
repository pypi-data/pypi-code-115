# -*- encoding: utf-8 -*-
# @Author: haogooder
# @Date:
# @Description:
from typing import Any, List, Dict

import yaml


class YAMLParserError(Exception):
    pass


class Parser(object):

    def __init__(self, yaml_path):
        if yaml_path is None or yaml_path.isspace():
            raise YAMLParserError("YAML File Path Cant Empty")
        self.path = yaml_path
        with open(self.path, "r") as f:
            self.values = yaml.safe_load(f)

    def get_value(self, keys=None) -> Any:
        if not isinstance(keys, str):
            raise TypeError()
        if keys is None:
            keys = ""
        if keys.strip() == "":
            return self.values
        key_list = keys.split(".")
        value = self.values
        for key in key_list:
            try:
                value = value[key]
            except KeyError:
                raise YAMLParserError("Yaml Dont Exist This Node [{}], The Original Keys: [{}]".format(key, keys))
        return value

    def get_str(self, keys=None) -> str:
        value = self.get_value(keys)
        if not isinstance(value, str):
            raise TypeError()
        return value

    def get_int(self, keys=None) -> int:
        value = self.get_value(keys)
        if not isinstance(value, int):
            raise TypeError()
        return value

    def get_bool(self, keys=None) -> bool:
        value = self.get_value(keys)
        if not isinstance(value, bool):
            raise TypeError()
        return value

    def get_float(self, keys=None) -> float:
        value = self.get_value(keys)
        if not isinstance(value, float):
            raise TypeError()
        return value

    def get_list(self, keys=None) -> List:
        value = self.get_value(keys)
        if not isinstance(value, List):
            raise TypeError()
        return value

    def get_dict(self, keys=None) -> Dict:
        value = self.get_value(keys)
        if not isinstance(value, Dict):
            raise TypeError()
        return value


def yaml_val(path, keys=None):
    """

    :param path:
    :param keys:
    :return:
    """
    yaml_process = Parser(path)
    return yaml_process.get_value(keys)


def yaml_cluster_str(path, keys):
    """
    YAML文件内容:
        <keys>:
            xxx:
                host: <host1>
                port: <port1>
            xxx:
                host: <host2>
                port: <host2>
    转换为:
        <host1>:<port1>,<host1>:<port1>

    :param path:
    :param keys:
    :return:
    """
    cluster_url = ''
    temp_value = Parser(path).get_value(keys)
    for node in temp_value:
        host_port_str = '{}:{}'.format(temp_value[node]['host'], temp_value[node]['port'])
        if not cluster_url and host_port_str:
            cluster_url = host_port_str
            continue
        if host_port_str:
            cluster_url = '{},{}'.format(cluster_url, host_port_str)
    return cluster_url


def yaml_cluster_list(path, keys):
    """
    YAML文件内容:
        <keys>:
            xxx:
                host: <host1>
                port: <port1>
            xxx:
                host: <host2>
                port: <host2>
    转换为:
        [ <host1>:<port1>, <host2>:<port2> ]

    :param path:
    :param keys:
    :return:
    """
    cluster_url = []
    temp_value = Parser(path).get_value(keys)
    for node in temp_value:
        host_port_str = '{}:{}'.format(temp_value[node]['host'], temp_value[node]['port'])
        if host_port_str:
            cluster_url.append(host_port_str)
    return cluster_url


def yaml_cluster_tuplue_list(path, keys):
    """
    YAML文件内容:
        <keys>:
            xxx:
                host: <host1>
                port: <port1>
            xxx:
                host: <host2>
                port: <host2>
    转换为:
        [ (<host1>, <port1>), (<host2>, <port2>) ]

    :param path:
    :param keys:
    :return:
    """
    cluster = []
    temp_value = Parser(path).get_value(keys)
    for node in temp_value:
        host = temp_value[node]['host']
        port = temp_value[node]['port']
        if host or port:
            cluster.append((host, port))
    return cluster


def yaml_cluster_map_list(path, keys):
    """
    YAML文件内容:
        <keys>:
            xxx:
                host: <host1>
                port: <port1>
            xxx:
                host: <host2>
                port: <host2>
    转换为:
        {
            {"host": <host1>, "port": <port1>},
            {"host": <host2>, "port": <port2>}
        }

    :param path:
    :param keys:
    :return:
    """
    cluster_map_list = []
    temp_value = Parser(path).get_value(keys)
    for node in temp_value:
        host_port_map = {"host": temp_value[node]['host'], "port": temp_value[node]['port']}
        cluster_map_list.append(host_port_map)
    return cluster_map_list


if __name__ == "__main__":
    pass
