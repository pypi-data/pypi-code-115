
from enum import Enum


class BigquerySchemaType(Enum):
    INTEGER = 'INTEGER'  # 整数
    NUMERIC = 'NUMERIC'  # 十进制
    BIGNUMERIC = 'BIGNUMERIC'  # 大十进制
    FLOAT = 'FLOAT'  # 浮点数
    STRING = 'STRING'  # 字符串
    DATETIME = 'DATETIME'  # 不推荐使用
    DATE = 'DATE'  # 不推荐使用
    TIMESTAMP = 'TIMESTAMP'  # 时间戳
