# -*- coding: utf-8 -*-
# @Time    : 2021/7/3 17:44
# @Author  : Beall
# @File    : Update_chromedriver.py
# @Software: win10 python3.7
import requests
import os
import time
import zipfile


def unzip_file(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        print('This is not zip')


def main():
    time_version_dict = {}  # 用来存放版本与时间对应关系
    time_list = []  # 用来存放时间列表

    web = requests.get('https://registry.npmmirror.com/-/binary/chromedriver/')
    for i in web.json():
        if i['type'] == 'dir' and i['name'] != 'icons/':
            time_list.append(i['modified'])
            time_version_dict[i['modified']] = i['name']

    latest_version = time_version_dict[max(time_list)]  # 用最大（新）时间去字典中获取最新的版本号
    download_url = 'http://npm.taobao.org/mirrors/chromedriver/' + latest_version + 'chromedriver_win32.zip'  # 拼接下载链接
    file = requests.get(download_url)
    with open("chromedriver.zip", 'wb') as zip_file:  # 保存文件到脚本所在目录
        zip_file.write(file.content)
    while True:
        if os.path.exists("chromedriver.zip"):
            unzip_file("chromedriver.zip", os.path.abspath(os.getcwd()))
            break
        else:
            time.sleep(1)
    print(f'{latest_version} 号版本chromedriver，最新修改时间为{max(time_list)} 已下载完成！\n文件已解压至: '
          f'{os.path.abspath(os.getcwd())}/chromedriver.exe')
    os.remove("chromedriver.zip")


if __name__ == '__main__':
    main()
