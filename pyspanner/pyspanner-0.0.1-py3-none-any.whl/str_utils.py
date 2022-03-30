# -*- encoding: utf-8 -*-
# @Author   :   haogooder
# @Date     :   2021/10/10
# @Desc     :   the description of this file
import ast
import gzip
import json

# 解压分片长度 （影响限制解压大小的情况）
DECOMPRESS_CHUNK_SIZE = 40960


class StringUtil(object):
    """
    封装了字符串相关的操作
    """

    @staticmethod
    def reverse_by_delimiter(original_str, delimiter):
        """
        根据分隔符反转字符串，可以用来反转域名（指定分隔符为"."）
        :param original_str:
        :param delimiter:
        :return:
        """
        reverse_str_list = reversed(original_str.split(delimiter))
        return delimiter.join(reverse_str_list)

    @staticmethod
    def safely_load_from(string, default_value=None):
        """
        安全地从某个字符串反序列化成python对象
        :param string:
        :param default_value:
        :return:
        """
        try:
            return json.loads(string)
        except (ValueError, TypeError):
            pass
        try:
            return ast.literal_eval(string)
        except (ValueError, SyntaxError):
            pass
        return default_value

    @staticmethod
    def gzip_compress(source):
        """
        compress string, default using gzip algorithm
        :param source:
        :return:
        """
        if isinstance(source, str):
            source = source.encode("utf-8")
        return gzip.compress(source)

    @staticmethod
    def gzip_decompress(source):
        """
        decompress string, default using gzip algorithm
        :param source:
        :return:
        """
        return gzip.decompress(source).decode('utf8')
