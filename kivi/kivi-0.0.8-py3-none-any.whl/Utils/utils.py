import os
import json
import time
import pickle
import logging
import numpy as np
import pandas as pd
from tqdm.notebook import tqdm_notebook
from IPython.display import display

from pyspark.sql.types import *
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def WarnInfo(info, disp=True):
    """
    描述：提示一些信息。
    """
    if disp:
        logging.warning(info)


def getNowDate():
    '''
    描述：返回当前日期
    format[YYYYMMDD]: 20200202

    示例：getNowDate()
    '''
    return time.strftime("%Y%m%d", time.localtime())

def convertColToList(df, col):
    """
    描述：convert pyspark DataFrame to list.

    参数：
    :param df: 需要转换的 df[PySpark DataFrame]
    :param col: 需要转换的字段名称 column name

    示例：

    """
    return df.select(col).rdd.map(lambda x: x[0]).collect()


def getFolders(path):
    """
    描述：返回路径下全部的文件夹
    """
    files = os.listdir(path)
    Folders = []
    for folder in files:
        if '.' not in folder and '_' not in folder:
            Folders.append(folder)
    return Folders

def saveCsv(df, csvName):
    """

    """
    if not os.path.exists('res'):
        os.mkdir('res')
    df.to_csv(os.path.join('res', csvName + '.csv'), index=False)

def convertDictToDataFrame(dataType):

    newDataType = {}
    lengthList = []

    for item in dataType.items():
        lengthList.append(len(item[1]))
    maxLength = max(lengthList)
    for key in dataType.keys():
        newDataType[key] = dataType.get(key) + [None] * (maxLength - len(dataType.get(key)))
    return pd.DataFrame(newDataType)

def sortColumns(dfCount) -> list:
    """
    给定多列不同列长的 df.count() 进行列的排序，形成上三角排列。

    :param dfCount: Series df.count()
    :return: new columns name
    """

    _dfNum = pd.DataFrame(dfCount, columns=['num'])
    _newCols = [sorted(group.index.to_list()) for i, group in _dfNum.groupby('num', sort=True)][::-1]
    newCols = []
    for item in _newCols:
        newCols += item
    return newCols

def sameLength(*args):
    """
    描述：

    参数：
    """
    length = [len(item) for item in args]
    if len(set(length)) == 1:
        return True
    else:
        Exception(ValueError, 'args must be same length!')

def mkdir(filename):
    """
    描述：检查文件路径是否存在，不存在的情况下创建路径。

    参数：
    :param filename: 文件路径
    :return: None
    """
    path = os.path.dirname(filename)
    if not os.path.exists(path):
        os.mkdir(path)

class Pk:
    """
    描述：写入与读取 `.pickle` 文件
    """
    @staticmethod
    def save(filename, data):
        """
        描述：保存数据至 .pickle 文件

        参数：
        :param filename: 保存文件路径
        :param data: 需要保存的数据
        :return: None
        """
        mkdir(filename)
        with open(filename, 'wb+') as f:
            pickle.dump(data, f)

    @staticmethod
    def load(filename):
        """
        描述：载入 .pickle 数据

        参数：
        :param filename: 文件路径
        :return: data .pickle 文件中的数据
        """
        with open(filename, 'rb') as f:
            data = pickle.load(f, encoding='gbk')
        return data

class Json:
    """
    描述：写入与读取 `.json` 文件
    """

    @staticmethod
    def save(filename, data):
        """
        描述：保存数据至 .json 文件

        参数：
        :param filename: 保存文件路径
        :param path: 需要保存的数据
        :return: None
        """
        mkdir(filename)
        data = json.dumps(data, ensure_ascii=False, indent=4)
        with open(filename, 'w+') as f:
            f.write(data)

    @staticmethod
    def load(filename):
        """
        描述：载入 .json 数据

        :param path: 文件路径
        :return: data .json 文件中的数据
        """
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
