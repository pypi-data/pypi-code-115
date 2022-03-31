# ======================
# -*- coding:utf-8 -*-
# @author:Beall
# @time  :2022/3/31 9:48
# @file  :setup.py.py
# ======================
from setuptools import setup

setup(
    name='ShareClass',  # 包名字
    version='1.0.2',  # 包版本
    description='A code base to python common function management!',  # 简单描述
    long_description='A code base to python common function management!',  # 简单描述
    author='beall',  # 作者
    author_email='beallhuang@163.com',  # 作者邮箱
    url='https://www.easylfe.com',  # 包的主页
    packages=['ShareClass'],  # 包
    platforms=['windows'],
    install_requires=['requests',
                      'Pillow'
                      'paramiko',
                      'bs4'],
    python_requires='>=3.6'
)
