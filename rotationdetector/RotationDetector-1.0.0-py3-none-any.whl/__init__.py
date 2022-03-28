# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    :   2022/3/27 20:19
# @Author  :   xidian wkx
# @File    :   __init__.py.py

from RotationDetector.checkDataFormat.checkDir import CheckDir
from RotationDetector.RotationModelYolov4 import RotationModel

from RotationDetector.train import Train
from RotationDetector.detect import Detect
from RotationDetector.test import Test
from RotationDetector.detect_onnx import detectOnOnnx

# 提供六个函数，分别是检查数据文件夹，模型初始化
CheckDir = CheckDir
RotationModel = RotationModel

# 提供训练，检测，测试功能
Train = Train
Detect = Detect
Test = Test
DetectOnOnnx = detectOnOnnx
