# ======================
# -*- coding:utf-8 -*-
# @author:Beall
# @time  :2022/1/14 13:51
# @file  :ftp_upload.py
# ======================
import paramiko
import datetime
import os


def upload(hostname, username, password, port, local_dir, remote_dir):
    img_list = []
    try:
        t = paramiko.Transport((hostname, port))
        t.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(t)
        print('upload file start %s ' % datetime.datetime.now())
        for root, dirs, files in os.walk(local_dir):
            # print('[%s][%s][%s]' % (root, dirs, files))
            detail_index = 0
            for filespath in files:
                if 'jpg' in filespath and 'detail' in filespath and detail_index < 7:
                    local_file = os.path.join(root, filespath)
                    # print(11, '[%s][%s][%s][%s]' % (root, filespath, local_file, local_dir))
                    a = local_file.replace(local_dir, '').replace('\\', '/').lstrip('/')
                    # print('01', a, '[%s]' % remote_dir)
                    remote_file = os.path.join(remote_dir, a)
                    # print(22, remote_file)
                    img_list.append(remote_file)
                    try:
                        sftp.put(local_file, remote_file)
                        sftp.chmod(remote_file, 0o705)
                    except Exception as e:
                        sftp.mkdir(os.path.split(remote_file)[0])
                        sftp.put(local_file, remote_file)
                        sftp.chmod(os.path.split(remote_file)[0], 0o705)
                        sftp.chmod(remote_file, 0o705)
                        # print("66 upload %s to remote %s" % (local_file, remote_file))
                    detail_index += 1
                elif 'jpg' in filespath and 'detail' not in filespath:
                    local_file = os.path.join(root, filespath)
                    # print(11, '[%s][%s][%s][%s]' % (root, filespath, local_file, local_dir))
                    a = local_file.replace(local_dir, '').replace('\\', '/').lstrip('/')
                    # print('01', a, '[%s]' % remote_dir)
                    remote_file = os.path.join(remote_dir, a)
                    # print(22, remote_file)
                    img_list.append(remote_file)
                    try:
                        sftp.put(local_file, remote_file)
                        sftp.chmod(remote_file, 0o705)
                    except Exception as e:
                        sftp.mkdir(os.path.split(remote_file)[0])
                        sftp.chmod(os.path.split(remote_file)[0], 0o705)
                        sftp.put(local_file, remote_file)
                        sftp.chmod(remote_file, 0o705)
        #                 print("66 upload %s to remote %s" % (local_file, remote_file))
        print('upload file success %s ' % datetime.datetime.now())
        t.close()
    except Exception as e:
        print(e)
    img_list = [i.replace('/www/wwwroot/', 'https://') for i in img_list]
    return img_list


if __name__ == '__main__':
    pass