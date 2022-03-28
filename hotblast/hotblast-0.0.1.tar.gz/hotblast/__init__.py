import configparser
import platform
import os

config_content = '''[DATA]
# 扫描文件夹路径
total_folder_path = D:/example
# 选择扫描文件夹或者文件 [文件夹:1,文件:2,全部:3]
select_file_or_folder = 3
# 日志文件编码
coding = gbk'''

new_path = os.getcwd() + "\\config.cfg"

def push():
    if os.path.exists(new_path):
        config = configparser.ConfigParser()
        config.read(new_path, encoding='utf-8')
        root_path = config.get("DATA", "total_folder_path")
        if root_path == "D:/example":
            print("请修改配置文件,再次初始化进行扫描。")
            if platform.system() == "Windows":
                os.system("explorer /select,%s" % (new_path))
        else:
            from .initialize import Initialize
            Initialize(new_path).run()


    else:
        print("初始化成功!")
        print("请修改配置文件,再次初始化进行扫描。")

        with open(new_path, mode='w', encoding='utf-8') as file:
            file.write(config_content)
        if platform.system() == "Windows":
            os.system("explorer /select,%s" % (new_path))

def modifty_conf():
    message = input("请输入扫描地址:")
    new_data = config_content.replace("D:/example",message)
    with open(new_path, mode='w', encoding='utf-8') as file:
        file.write(new_data)

def del_conf():
    os.system('''del /f /q %s
    del /f /q %s'''%(new_path,os.getcwd() + "\\info"))



def finding():
    if os.path.exists(new_path):
        config = configparser.ConfigParser()
        config.read(new_path, encoding='utf-8')
        root_path = config.get("DATA", "total_folder_path")
        if root_path == "D:/example":
            pass
        else:
            from .Search import main
            main(new_path)
