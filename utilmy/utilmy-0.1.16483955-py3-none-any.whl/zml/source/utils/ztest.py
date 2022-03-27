# -*- coding: utf-8 -*-
"""

Basic tests

"""
import copy
import os
from collections import OrderedDict

import dateutil
import numpy as np
import pandas as pd
import scipy as sci

import sklearn as sk
from sklearn import covariance, linear_model, model_selection, preprocessing
from sklearn.cluster import dbscan, k_means
from sklearn.decomposition import PCA, pca
from sklearn.discriminant_analysis import (LinearDiscriminantAnalysis,
                                           QuadraticDiscriminantAnalysis)
from sklearn.ensemble import (AdaBoostClassifier, ExtraTreesClassifier,
                              GradientBoostingClassifier,
                              RandomForestClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, make_scorer,
                             mean_absolute_error, roc_auc_score, roc_curve)
from sklearn.model_selection import (GridSearchCV, cross_val_score,
                                     train_test_split)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

# from attrdict import AttrDict as dict2
# from kmodes.kmodes import KModes
# from tabulate import tabulate


try:
    from catboost import CatBoostClassifier, Pool, cv
except Exception as e:
    print(e)


####################################################################################################
print(os.getcwd())


####################################################################################################
class dict2(object):
    def __init__(self, d):
        """ dict2:__init__
        Args:
            d:     
        Returns:
           
        """
        self.__dict__ = d




####################################################################################################
from dsa.da.util_feature import pd_colnum_tocat

"""
pd_colnum_tocat(
    df, colname=None, colexclude=None, colbinmap=None, bins=5, suffix="_bin",
    method="uniform", na_value=-1, return_val="dataframe,param",
)
"""



























