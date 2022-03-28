# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    :   2022/3/27 22:09
# @Author  :   xidian wkx
# @File    :   Config.py

class Config:
    '''
    训练参数配置
    Args：
        1.trainFloder：训练目录，可通过setTrainFloder设定

        2.weightsPreTrainedPath：预训练权重目录，可通过setPreTrainedWeightPath设定

        3.TrainWeightPath：训练权重保存目录，可通过setTrainWeightPath设定

        4.numClasses：检测类别，可通过setNumberClasses设定

        其他参数为训练超参，不建议设置
    '''
    def __init__(self, trainFloder = None, weightsPreTrainedPath = None, TrainWeightPath = None, numClasses = None):
        self.trainFloder = trainFloder
        self.weightsPreTrainedPath = weightsPreTrainedPath
        self.TrainWeightPath = TrainWeightPath
        self.numClasses = numClasses

        self.epochs = 1
        self.lr = 0.0001
        self.batch_size = 1
        self.subdivisions = 1
        self.image_size = 608

    def setTrainFloder(self, trainFloder):
        self.trainFloder = trainFloder

    def setPreTrainedWeightPath(self,weightsPreTrainedPath):
        self.weightsPreTrainedPath = weightsPreTrainedPath

    def setTrainWeightPath(self, TrainWeightPath):
        self.TrainWeightPath = TrainWeightPath

    def setNumberClasses(self, numClasses):
        self.numClasses = numClasses

    def setEpochs(self, epochs):
        self.epochs = epochs

    def setLr(self, lr):
        self.lr = lr

    def setBatchSize(self, batchSize):
        self.batch_size = batchSize

    def setSubdivisions(self, subdivisions):
        self.subdivisions = subdivisions

    def setImageSize(self, imageSize):
        self.image_size = imageSize

class DectctConfig:
    def __init__(self):
        self.weights_path = None
        self.detectFile = None
        self.NumClasses = None
        self.className = []

        self.confThres = 0.85
        self.numThres = 0.1
        self.batchSize = 1
        self.imgSize = 608

    def setDetectFile(self,detectFile):
        self.detectFile = detectFile

    def setWeights_path(self,weights_path):
        self.weights_path = weights_path

    def setNumClasses(self, NumClasses):
        self.NumClasses = NumClasses

    def setClassName(self, className):
        self.className = className

    def setConfThres(self,confThres):
        self.confThres = confThres

    def setNumThres(self, numThres):
        self.numThres = numThres

    def setBatchSize(self, batchSize):
        self.batchSize = batchSize

    def setImgSize(self, imgSize):
        self.imgSize = imgSize
