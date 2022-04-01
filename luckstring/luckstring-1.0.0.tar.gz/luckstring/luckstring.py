#！/usr/bin/python
# -*- coding:utf-8 -*-
# author : 9304.com

def split(src, sp, ignore=True):
    """ 
    @src 原字符串
    @sp 字符串的分割字符
    @ignore 分割字符串时sp是否大小写敏感 (False:敏感, 默认忽略大小写)
    """
    # src = ""
    # sp = ""
    if ignore:
        ret = []
        upper_sp = sp.upper()
        upper_src = src.upper()
        s_start = 0
        
        src_len = len(upper_src)
        sp_len = len(upper_sp)

        i = 0
        while(i<src_len-sp_len):
        # for i in range(0, src_len-sp_len):
            match = True
            for p in range(0, sp_len):
                if upper_src[i+p:i+p+1] != upper_sp[p:p+1]:
                    match =False
                    break
            if match:
                ret.append( src[s_start:i])
                
                s_start = i + sp_len
                i =i + sp_len
            else:
                i =i + 1
            pass

        ret.append( src[s_start:])

    else:
        ret = src.split(sp)
    return ret


