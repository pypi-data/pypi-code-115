# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    :   2022/3/27 12:35
# @Author  :   xidian wkx
# @File    :   checkDir.py

import glob
import os
import warnings
import numpy as np

class CheckDir:
    '''
    检查数据是否符合标准
    为了解耦和多样，数据格式如下：
    \filename
        |-\file01
            |-name1.png
            |-name1.txt
            ...
            |-namen.png
            |-namen.txt
        |-\file02
            |-name1.png
            |-name1.txt
            ...
            |-namen.png
            |-namen.txt
        ...
        ...
        |-\filen
    filename:某一个检测任务的数据集
    file01--n：该检测任务下，需要检测的缺陷标记文件夹，例如
            --file01为缺口数据和对应标记
            --file02为裂纹数据和对应标记
    name.png：需要检测的图片，为了规范化，对于每一个图片，必须存在对应的标记文件
    name.txt：需要检测的图片对应的标记
    '''
    def __init__(self, fileName):
        self.fileName = fileName
        self.__subFileFolder = self.__getAllSubFolder()

    def __getAllSubFolder(self):
        '''
        获取所有data文件夹下的子文件夹
        如果存在非文件夹：报错
        如果某个文件夹没数据：报错
        Returns: 返回子文件夹列表
        '''
        subFileFolder = []
        for subDir in os.listdir(self.fileName):
            subDirPath = os.path.join(self.fileName,subDir)
            if os.path.isdir(subDirPath):
                subFileFolder.append(subDirPath)
            else:
                message = "\n数据文件夹{}下存在非子文件夹数据".format(self.fileName)
                warnings.warn(message)
                exit(1)
        return subFileFolder


    def __getAllSubLabelImage(self, subFileFolder):
        '''
        函数功能：获取subFileFolder下的所有文件
        Args:
            subFileFolder: 子文件夹名
        Returns:子文件夹下所有png图片
        '''
        return [pngPath.split(".png")[0] for pngPath in glob.glob("{}\*png".format(subFileFolder))]

    def __getAllSubLabelTxt(self, subFileFolder):
        '''
        函数功能：获取subFileFolder下的所有标记数据
        Args:
            subFileFolder: 子文件夹名
        Returns:子文件夹下所有txt文本
        '''
        return [txtPath.split(".txt")[0] for txtPath in glob.glob("{}\*txt".format(subFileFolder))]

    def __jedgeIllegalTxt(self, subFolderLabelPath):
        '''
        函数功能：判断传递进来的txt文本是否合法
        Args:
            subFolderLabelPath: 文本路径
        Returns:
            返回是否非法
        '''
        data = np.loadtxt(subFolderLabelPath)

        dataLineCount = len(data)
        dataCount = data.size

        # txt为空，则非法
        if (dataLineCount == 0):
            return True
        # txt内标记数据有误，则非法
        else:
            if (dataCount % 8 != 0):
                return True
        return False


    def __serachImageWithIllegalTxt(self, subFolderIamgeList: list, subFolderLabelList: list):
        '''
        函数功能：返回subFolderIamgeList中不存在对应标记、以及标记有问题的图片
        Args:
            subFolderIamgeList: 图片文件路径列表
            subFolderLabelList: 标记数据路径列表
        Returns:
            ImageWithNoLabel：不存在标记的图片
            ImageWithEmptyLabel：不符合格式的文本
        '''
        ImageWithNoLabel = []
        ImageWithIllegalLabel = []

        for subFolderIamgePath in subFolderIamgeList:
            if not subFolderIamgePath in subFolderLabelList:
                ImageWithNoLabel.append(subFolderIamgePath+"png")

            else:
                subFolderIamgeLabelPath = subFolderIamgePath + ".txt"
                # 如果不合法
                if(self.__jedgeIllegalTxt(subFolderIamgeLabelPath)):
                    ImageWithIllegalLabel.append(subFolderIamgeLabelPath)
        return ImageWithNoLabel, ImageWithIllegalLabel

    def doValite(self):
        '''
        函数功能：进行规范化验证
        Returns:
            如果通过验证，返回Ture，反之Flase
        '''
        ImageWithNoLabel = []
        ImageWithIllegalLabel = []
        # 遍历每一个子文件夹
        for subFolder in self.__getAllSubFolder():
            subFolderIamgeList = self.__getAllSubLabelImage(subFolder)
            subFolderLabelList = self.__getAllSubLabelTxt(subFolder)
            # 查找非法数据
            subFolderImageWithNoLabel, subFolderImageWithIllegalLabel = self.__serachImageWithIllegalTxt(subFolderIamgeList, subFolderLabelList)
            ImageWithNoLabel.extend(subFolderImageWithNoLabel)
            ImageWithIllegalLabel.extend(subFolderImageWithIllegalLabel)
        if len(ImageWithNoLabel) == 0 and len(ImageWithIllegalLabel) == 0:
            return True
        else:
            warnings.warn("数据格式不合法:\n")
            if(len(ImageWithNoLabel) != 0):
                message = "找到不含有对应标记数据的png图片，如下：\n{}".format(ImageWithNoLabel)
                warnings.warn(message)
            if(len(ImageWithIllegalLabel) != 0):
                message = "含有非法标记数据txt如下：\n{}".format(ImageWithIllegalLabel)
                warnings.warn(message)
            return False



