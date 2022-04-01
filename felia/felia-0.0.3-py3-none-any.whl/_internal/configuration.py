import configparser
import os

from pip._vendor.platformdirs.windows import Windows


win = Windows()

DIR_NAME = "felia"

config = configparser.ConfigParser()
ini = win.user_config_path / DIR_NAME / 'felia.ini'
config.read(ini, encoding='utf-8')


class ConfMixin:
    def change_workdir(self):
        section = config[self.__class__.__name__.upper()]
        projects = list(section.items())

        if len(projects) == 1:
            path = projects[0][1]
        else:
            for index, value in enumerate(projects):
                print(index + 1, value[0])

            i = int(input("请选择一个项目")) - 1
            path = projects[i][1]

        print("切换路径:", path)
        os.chdir(path)