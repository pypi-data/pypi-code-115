# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    :   2022/3/26 16:49
# @Author  :   xidian wkx
# @File    :   CvTool.py

import os
import glob
import cv2
import warnings

class CvTool:
    '''
    该类主要用于图片在进行标注之前的规范化
    ImageDir：所需要标注图片的文件路径，不可包含中文
    CropImage：主要针对喇叭口图片的中间部位裁剪出来
    '''
    def __init__(self, imageDir, cropImage: bool = True):
        self.imageDir  = imageDir
        self.cropImage = cropImage

        self.__saveDir   = "{}Resize".format(imageDir)
        self.__imageList = []
        self.__imageSize = 1000

    def setImageSize(self, imageSize):
        self.__imageSize = imageSize

    def getImageSize(self):
        return self.__imageSize

    def getImageList(self):
        self.__extendImageList()
        return self.__imageList

    @classmethod
    def loadImageDir(cls, imageDir, cropImage: bool = True):
        '''
        推荐使用构造器的方式进行初始化,可以验证合法化
        '''
        cls.validate(imageDir)
        return cls(imageDir, cropImage)

    @staticmethod
    def validate(imageDir: str):
        '''
        验证文件夹是否合法
        1.如果包含中文路径，则非法
        2.如果文件夹不存在，则非法
        '''
        def is_contains_chinese(strs):
            for _char in strs:
                if '\u4e00' <= _char <= '\u9fa5':
                    return False
            return True
        assert os.path.isdir(imageDir)
        assert is_contains_chinese(imageDir)

    # 获取所有图片
    def __extendImageList(self):
        self.__imageList.extend(glob.glob("{}/*png".format(self.imageDir)))
        self.__imageList.extend(glob.glob("{}/*jpg".format(self.imageDir)))

    # 读取灰度图片
    def __read_image(self, filepath):
        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        return img

    # resize大小为统一格式
    def __resize_image(self, img):
        return cv2.resize(img, (self.__imageSize, self.__imageSize))

    # 进行单个图片的裁剪
    def __detect_and_crop(self, img):
        """定位喇叭口并裁剪出目标区域"""
        img1 = img

        # 先来个巨大的滤波，磨磨皮方便边缘检测
        img1 = cv2.blur(img1, (3, 3))
        img1 = cv2.blur(img1, (15, 15))
        img1 = cv2.blur(img1, (49, 49))

        # 进行边缘检测
        img1 = cv2.Canny(img1, 3, 9, 3)

        # 形态学操作一下，让目标区域更明显
        # 先小腐蚀然后膨胀，去掉一些噪声，然后再腐蚀再巨大膨胀，增大些目标区域
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
        img1 = cv2.morphologyEx(img1, cv2.MORPH_CLOSE, kernel)
        img1 = cv2.erode(img1, None, iterations=4)
        img1 = cv2.dilate(img1, None, iterations=4)
        img1 = cv2.erode(img1, None, iterations=4)
        img1 = cv2.dilate(img1, None, iterations=4)
        img1 = cv2.erode(img1, None, iterations=4)
        img1 = cv2.dilate(img1, None, iterations=20)

        # 找出轮廓
        contours, _ = cv2.findContours(img1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        max_contours = sorted(contours, key=cv2.contourArea, reverse=True)[0]
        rect = cv2.boundingRect(max_contours)
        rect = list(rect)
        rect[0] = max(rect[0] - 50, 0)
        rect[1] = max(rect[1] - 50, 0)
        rect[2] = min(rect[2] + 100, img1.shape[0] - 1)
        rect[3] = min(rect[3] + 100, img1.shape[1] - 1)

        # 图片裁剪
        img1 = img[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]

        return img1

    def standardization(self):
        '''
        进行图片标准化
        '''
        if not (os.path.exists(self.__saveDir)):
            os.mkdir(self.__saveDir)

        if not len(self.getImageList()):
            warnings.warn('没有标准化任何图片，请检查格式，确定图片为png,jpg')

        if self.cropImage:
            for imagePath in self.getImageList():
                img = self.__resize_image(self.__detect_and_crop(self.__read_image(imagePath)))
                cv2.imwrite(imagePath.replace("jpg", "png").replace(self.imageDir, self.__saveDir), img)
        else:
            for imagePath in self.getImageList():
                cv2.imwrite(imagePath.replace("jpg", "png").replace(self.imageDir, self.__saveDir), self.__resize_image(self.__read_image(imagePath)))




