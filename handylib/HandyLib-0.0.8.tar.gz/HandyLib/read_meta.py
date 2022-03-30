#coding=utf-8
'''
read meta info from file
'''
import pyexiv2
import os,time
def print_create_date(path_to_file):
    t = time.ctime(os.path.getctime(path_to_file))
    print(t)

def print_modify_date(path_to_file):
    t = time.ctime(os.path.getmtime(path_to_file))
    print(t)

def get_create_date(path_to_file):
    return os.path.getctime(path_to_file)

def get_modify_date(path_to_file):
    return os.path.getmtime(path_to_file)

def get_img_meta(path_to_img,encoding='GBK'):
    '''
    by default, work for windows, change encoding if cannot locate file
    '''
    img = pyexiv2.Image(path_to_img,encoding)
    iptc =  img.read_iptc()
    exif = img.read_exif()
    comment = img.read_comment()
    icc = img.read_icc()
    raw_xmp = img.read_raw_xmp()
    xmp = img.read_xmp()
    img.close()
    return iptc,exif,comment,icc,raw_xmp,xmp