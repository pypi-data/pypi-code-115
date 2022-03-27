# -*- coding: utf-8 -*-
# @Time    : 2020/6/5 12:14
# @Author  : Chensy Cao
# @Email   : chensy.cao@zjtlcb.com
# @FileName: iv.py
# @Software: PyCharm

import numpy as np
import pandas as pd
from scipy.stats import beta
import matplotlib.pyplot as plt


class BetaDistribution:

    def __init__(self, Alpha: float = None, Beta: float = None):
        self.Alpha = Alpha
        self.Beta = Beta

    def grade_rate(self, target_grade: int):
        """
        计算 Beta 分布下，每个评级等级的比率
        :return:
        """
        target_grade_rate, CDF = [], []
        for i in range(target_grade):
            F_left = beta.cdf(x=(i / (target_grade)), a=self.Alpha, b=self.Beta, loc=0, scale=1)
            F_right = beta.cdf(x=((i + 1) / (target_grade)), a=self.Alpha, b=self.Beta, loc=0, scale=1)
            target_grade_rate.append(F_right - F_left)
            CDF.append(F_right)
        return target_grade_rate, CDF
