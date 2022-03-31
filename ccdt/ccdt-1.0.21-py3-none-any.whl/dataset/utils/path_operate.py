# -*- coding: utf-8 -*-
# @Time : 2022/3/25 13:47
# @Author : Zhan Yong
import os
from pathlib import Path


class PathOperate(object):

    def __init__(self, *args, **kwargs):
        """
        初始化方法
        :param args: 元组类型取值顺序，跟传参顺序有关
        :param kwargs:
        """
        self.dir_name = args[0]
        self.object_type = args[1]
        self.file_formats = args[2]
        self.coco_file = args[3]
        self.dir_paths = self.get_dir_paths()

    def get_valid_paths(self):
        """
        基础方法，不被使用，用于参考
        :return:
        """
        files_name = list()  # 返回文件名列表
        # 使用系统方法，递归纵向遍历根路径、子路径、文件
        for root, dirs, files in os.walk(self.dir_name, topdown=True):
            # 对目录和文件进行升序排序
            dirs.sort()
            files.sort()
            # 遍历文件名称列表
            for file in files:
                # 获取文件后缀
                file_suffix = os.path.splitext(file)[-1]
                # 如果读取的文件后缀，在指定的后缀列表中，则返回真继续往下执行
                if file_suffix in self.file_formats:
                    # 如果文件在文件列表中，则返回真继续往下执行
                    files_name.append(file)

        return files_name

    def get_dir_paths(self):
        """
        递归组合labelme数据集指定目录路径
        :return:
        """
        path_name = list()  # 文件夹路径
        for root, dirs, files in os.walk(self.dir_name, topdown=True):
            # print(root)
            obj_path = Path(root)
            input_data_format = dict(
                type='',
                images_dir='',
                labelme_dir='',
                file_formats='',
                coco_file='',
                input_dir=''
            )
            dirs.sort()
            files.sort()
            if self.object_type == 'BaseLabelme':
                for dir_name in dirs:
                    input_data_format['file_formats'] = self.file_formats
                    input_data_format['coco_file'] = self.coco_file
                    if dir_name == '00.images' or dir_name == '01.labelme':
                        # print(root)
                        replace_path = root.replace(self.dir_name, '').strip('\\/')
                        image_labelme_path = str(obj_path.joinpath(root, dir_name))
                        input_data_format['input_dir'] = self.dir_name
                        if '00.images' in image_labelme_path:
                            input_data_format['images_dir'] = os.path.join(replace_path, dir_name)
                            input_data_format['type'] = self.object_type
                        if '01.labelme' in image_labelme_path:
                            input_data_format['labelme_dir'] = os.path.join(replace_path, dir_name)
                            input_data_format['type'] = self.object_type
                if input_data_format.get('labelme_dir') != '' and input_data_format.get('images_dir') != '' and \
                        input_data_format['type'] != '' and input_data_format['file_formats'] != '' and \
                        input_data_format['input_dir'] != '':
                    path_name.append(input_data_format)
            # 针对coco转labelme，只需要输入图片路径的时候，进入如下逻辑条件
            if self.object_type == 'Coco':
                input_data_format['type'] = self.object_type
                input_data_format['input_dir'] = obj_path.parent
                input_data_format['images_dir'] = os.path.join(obj_path.name, '00.images')
                input_data_format['labelme_dir'] = os.path.join(obj_path.name, '01.labelme')
                input_data_format['coco_file'] = self.coco_file
                input_data_format['file_formats'] = self.file_formats
                path_name.append(input_data_format)
                return path_name
        return path_name

    @classmethod
    def get_files_paths(cls, dir_name, file_formats, input_dir):
        """
        递归组合指定文件格式路径
        :param input_dir:
        :param dir_name:
        :param file_formats:
        :return:
        """
        files_name = list()  # 返回文件名列表
        PathOperate.initialize(input_dir).joinpath(dir_name)
        for root, dirs, files in os.walk(os.path.join(input_dir, dir_name), topdown=True):
            # 对目录和文件进行升序排序
            dirs.sort()
            files.sort()
            # 遍历文件名称列表
            for file in files:
                # 获取文件后缀
                file_suffix = os.path.splitext(file)[-1]
                # 如果读取的文件后缀，在指定的后缀列表中，则返回真继续往下执行
                if file_suffix in file_formats:
                    # 如果文件在文件列表中，则返回真继续往下执行
                    files_name.append(file)
        return files_name

    @classmethod
    def initialize(cls, images_dir):
        """
        路径实列对象初始化
        :param images_dir:
        :return:
        """
        obj_dir = Path(images_dir)
        return obj_dir

    @classmethod
    def get_videos_path(cls, root_dir, file_formats):
        # dir_name_list = list()  # 文件夹名称
        # files_name = list()  # 文件名称
        # path_name = list()  # 文件夹路径
        file_path_name = list()  # 文件路径
        for root, dirs, files in os.walk(root_dir, topdown=True):
            dirs.sort()
            files.sort()
            # for dir_name in dirs:
            # if dir_name != '00.images' and dir_name != '01.labelme':
            # dir_name_list.append(dir_name)
            # 遍历文件名称列表
            for file in files:
                # 获取文件后缀
                file_suffix = os.path.splitext(file)[-1]
                # 如果读取的文件后缀，在指定的后缀列表中，则返回真继续往下执行
                if file_suffix in file_formats:
                    # 如果文件在文件列表中，则返回真继续往下执行
                    # files_name.append(file)
                    # path_name.append(root)
                    file_path_name.append(os.path.join(root, file))
        return file_path_name
