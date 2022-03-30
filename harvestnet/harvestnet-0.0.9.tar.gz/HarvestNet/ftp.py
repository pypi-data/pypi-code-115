import os
import ftplib
ftp = ftplib.FTP()
host ='47.94.218.159'
userName='model'
passWord ='a7x2t8NZRKGnnFh6'
port = 21
timeout = 100
ftp.connect(host, port, timeout)
ftp.login(userName, passWord)
ftp.encoding='gb18030'

basepath = os.path.dirname(__file__)
print(basepath)
allFileName = ftp.nlst()
model_list = allFileName[2:]
print('模型列表:' + model_list)
i = 0
for lists in allFileName[2:]:
    print('开始下载:' + lists)
    if i < 3:
      file_handler = open(basepath + '/' + model_list[i], 'wb')
      ftp.retrbinary('RETR ' + lists, file_handler.write)
      i = i + 1
      print('下载完成:' + lists)
    else:
        pass












