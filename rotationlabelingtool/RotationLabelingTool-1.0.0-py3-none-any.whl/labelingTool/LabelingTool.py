
from RotationLabelingTool.ui import UI
import cv2
import glob
import os
from PyQt5 import QtWidgets, QtGui, QtCore

from PyQt5.QtCore import *


class LabelingTool(QtWidgets.QMainWindow, UI):

    def __init__(self):
        super().__init__()
        self.setupUi(self)


        self.currLabelFilePath = None
        self.drawPoint = []

        self.DirPathLineEdit.setEnabled(False)
        self.OpenDirButton.clicked.connect(self.openDir)
        self.ImageListWidget.itemDoubleClicked.connect(self.startLabeling)

        self.PreviousImageButton.clicked.connect(self.openPreviousImage)
        self.NextImageButton.clicked.connect(self.openNextImage)
        self.ImageLabel.mousePressEvent = self.__drawClick
        self.DeleteBboxButton.clicked.connect(self.deleteBox)
        self.ClearBboxButton.clicked.connect(self.deleteAllBox)
        self.SaveBboxButton.clicked.connect(self.saveLabelInfo)
        pass

    def __drawClick(self, event: QtGui.QMouseEvent):
        x = event.x()
        y = event.y()
        self.drawPoint.append((x, y))
        if len(self.drawPoint) < 4:
            painter = QtGui.QPainter(self.imageQtPixmap)
            pen = QtGui.QPen()
            pen.setWidth(5)
            pen.setColor(QtGui.QColor("#00FF00"))
            painter.setPen(pen)
            painter.drawPoint(x, y)
            painter.end()
            self.ImageLabel.setPixmap(self.imageQtPixmap)
        else:
            # 映射回原图片坐标
            w_scale = self.imageCv.shape[1] / self.imageQtPixmap.width()
            h_scale = self.imageCv.shape[0] / self.imageQtPixmap.height()

            points = []
            for point in self.drawPoint:
                points.append((int(point[0] * w_scale), int(point[1] * h_scale)))
            self.drawPoint = []
            self.bBoxData.append(tuple(points))
            self.__updateBbox()

            self.__drawBox(self.imageCv, points)

            self.imageQt = self.__CvImage2Qt(self.imageCv)
            self.imageQtPixmap = QtGui.QPixmap.fromImage(self.imageQt).scaled(
                self.ImageLabel.width(), self.ImageLabel.height(), QtCore.Qt.IgnoreAspectRatio)
            self.ImageLabel.setPixmap(self.imageQtPixmap)
        pass

    def __drawBox(self, Cvimage, points):
        assert len(points) == 4
        cv2.line(Cvimage, points[0], points[1], (0, 255, 0), 5)
        cv2.line(Cvimage, points[1], points[2], (0, 255, 0), 5)
        cv2.line(Cvimage, points[2], points[3], (0, 255, 0), 5)
        cv2.line(Cvimage, points[3], points[0], (0, 255, 0), 5)
        pass

    def __updateBbox(self):
        self.BboxListWidget.clear()
        for _ in self.bBoxData:
            self.BboxListWidget.addItem(str(_))

    def __getImageFilePathList(self,dirPath):
        '''
        函数功能：检查是否存在图片
        是：返回
        不是：警告
        '''
        imageFilePathList = glob.glob('{}/*.png'.format(dirPath))
        if imageFilePathList:
            return imageFilePathList
        qWarning("该文件夹下不存在图片，请检查")

    def __displayImageListWidget(self, imageFileList):
        '''
        函数功能：将图片名字显示在ImageListWidget上
        '''
        self.ImageListWidget.clear()
        for one_file in imageFileList:
            self.ImageListWidget.addItem(one_file)

    def __readExitLabelFile(self, LabelFilePath):
        pass

    def __saveLabelInfo(self, LabelFilePath):
        '''
        函数功能：保存数据到txt文件，直接触发条件是点击保存
        但是在点击下一个，上一个时，也进行保存
        '''
        with open(LabelFilePath, 'w') as f:
            for bbox in self.bBoxData:
                f.write('{} {} {} {} {} {} {} {}\n'.format(
                    bbox[0][0] / 1000, bbox[0][1] / 1000,
                    bbox[1][0] / 1000, bbox[1][1] / 1000,
                    bbox[2][0] / 1000, bbox[2][1] / 1000,
                    bbox[3][0] / 1000, bbox[3][1] / 1000,
                ))
        self.statusbar.showMessage('{} 已保存'.format(LabelFilePath))

    def __drawBox(self, Cvimage, points):
        '''
        函数功能：框框绘制，必须是[[],[],[],[]]的形式
        '''
        assert len(points) == 4
        cv2.line(Cvimage, points[0], points[1], (0, 255, 0), 5)
        cv2.line(Cvimage, points[1], points[2], (0, 255, 0), 5)
        cv2.line(Cvimage, points[2], points[3], (0, 255, 0), 5)
        cv2.line(Cvimage, points[3], points[0], (0, 255, 0), 5)
        pass

    def __redrawQt(self):
        '''
        函数功能：重新利用self.bBoxData绘制
        如果删除某一个标注或者删除所有标注
        '''
        if self.currLabelFilePath == None:
            return
        self.imageCv = cv2.imread(self.currImageFilePath, cv2.IMREAD_COLOR)
        for bbox in self.bBoxData:
            self.__drawBox(self.imageCv, bbox)
        self.imageQt = self.__CvImage2Qt(self.imageCv)
        self.imageQtPixmap = QtGui.QPixmap.fromImage(self.imageQt).scaled(
            self.ImageLabel.width(), self.ImageLabel.height(), QtCore.Qt.IgnoreAspectRatio)
        self.ImageLabel.setPixmap(self.imageQtPixmap)
        pass

    def __CvImage2Qt(self, Cvimage):
        """将OpenCV格式的图像转换为QImage，方便进行显示"""
        if len(Cvimage.shape) == 2:
            # 转化灰色图像为彩色图像
            Cvimage = cv2.cvtColor(Cvimage, cv2.COLOR_GRAY2BGR)
            pass
        Cvimage = cv2.cvtColor(Cvimage, cv2.COLOR_BGR2RGB)
        height, width, channels = Cvimage.shape
        bytes_per_line = width * channels
        qtImage = QtGui.QImage(Cvimage, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        return qtImage


    def openDir(self):
        '''
        函数功能：
        1.打开对应的图片文件夹，其中图片格式标准为png，1000*1000
        2.开始标注
        '''
        self.dirPath = QtWidgets.QFileDialog.getExistingDirectory(self, '选择图片文件夹')
        if not self.dirPath:
            qWarning("文件夹不存在")
        # 获取所有图片路径和图片名字放到列表
        self.imageFilePathList = self.__getImageFilePathList(self.dirPath)
        self.imageFileList = [os.path.split(x)[-1] for x in self.imageFilePathList]
        # 将图片名字展示，开始标记，首先选中第一个
        self.__displayImageListWidget(self.imageFileList)
        currIndex = 0
        self.ImageListWidget.item(currIndex).setSelected(True)
        self.startLabeling()

    def startLabeling(self):
        '''
        函数功能：开始标记当前索引的图片
        第一步：刷新显示列表、获取图片名字和路径、构建txt标记文本、显示图片
        第二步：判断该图片对应的标记文件是否存在，若存在：读取并显示
        '''
        # 这里做判断主要是为了在点击下一个或者上一个时，将结果保存
        if self.currLabelFilePath != None:
            self.__saveLabelInfo(self.currLabelFilePath)
        # 预备工作：刷新显示列表、获取图片名字和路径、构建txt标记文本、显示图片
        self.BboxListWidget.clear()
        self.currImageFilename = self.ImageListWidget.selectedItems()[0].text()
        self.currImageFilePath= self.imageFilePathList[self.imageFileList.index(self.currImageFilename)]
        self.currLabelFilePath = self.currImageFilePath.replace("png", "txt")

        # 在QT上绘制并且显示图片
        self.imageCv = cv2.imread(self.currImageFilePath, cv2.IMREAD_COLOR)
        self.imageQT = self.__CvImage2Qt(self.imageCv)
        self.imageQtPixmap = QtGui.QPixmap.fromImage(self.imageQT).scaled(self.ImageLabel.width(), self.ImageLabel.height(), QtCore.Qt.IgnoreAspectRatio)
        self.ImageLabel.setPixmap(self.imageQtPixmap)

        # 如果标记文件已经存在，那就初始化bbox_data并添加标记数据，显示
        self.bBoxData = []
        if os.path.exists(self.currLabelFilePath):
            with open(self.currLabelFilePath) as f:
                for i, line in enumerate(f):
                    tmp = line.strip().split()
                    if len(tmp) != 8:
                        continue
                    self.bBoxData.append((
                        (int(float(tmp[0]) * 1000), int(float(tmp[1]) * 1000)),
                        (int(float(tmp[2]) * 1000), int(float(tmp[3]) * 1000)),
                        (int(float(tmp[4]) * 1000), int(float(tmp[5]) * 1000)),
                        (int(float(tmp[6]) * 1000), int(float(tmp[7]) * 1000))
                    ))
            if len(self.bBoxData) > 0:
                self.__updateBbox()
                self.__redrawQt()

    def openNextImage(self):
        '''
        函数功能：打开下一个图片
        '''
        cur_select_index = self.imageFileList.index(self.ImageListWidget.selectedItems()[0].text())
        if cur_select_index < len(self.imageFileList) - 1:
            self.ImageListWidget.item(cur_select_index + 1).setSelected(True)
            self.ImageListWidget.scrollToItem(self.ImageListWidget.item(cur_select_index + 1))
            self.startLabeling()
        pass

    def openPreviousImage(self):
        '''
        函数功能：打开上一个图片
        '''
        cur_select_index = self.imageFileList.index(self.ImageListWidget.selectedItems()[0].text())
        if cur_select_index > 0:
            self.ImageListWidget.item(cur_select_index - 1).setSelected(True)
            self.ImageListWidget.scrollToItem(self.ImageListWidget.item(cur_select_index - 1))
            self.startLabeling()
        pass

    def saveLabelInfo(self):
        '''
        函数功能：保存当前结果
        '''
        self.__saveLabelInfo(self.currLabelFilePath)

    def deleteBox(self):
        '''
        函数功能：删除某个框框
        '''
        # 清理绘制点
        self.drawPoint = []
        # 获取index
        selected = self.BboxListWidget.selectedIndexes()
        if len(selected) <= 0:
            return
        selected_idx = selected[0].row()
        # 删除index
        del self.bBoxData[selected_idx]
        # 刷新，重画
        self.__updateBbox()
        self.__redrawQt()
        pass


    def deleteAllBox(self):
        '''
        函数功能：删除所有框框
        '''
        self.drawPoint = []
        self.bBoxData = []
        self.__updateBbox()
        self.__redrawQt()
        pass

