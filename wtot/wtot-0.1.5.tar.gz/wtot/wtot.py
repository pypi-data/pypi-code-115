import os, sys
import re
import json
import time
import getopt
import random
import hashlib
import requests

from unittest import result
from collections import namedtuple
from termcolor import cprint, colored
from urllib.parse import quote

appid = '20220325001140552'
secretKey = 'LiIWn_rNJrbLErVu6sGT'

def get_myurl(words,fromLang='auto',toLang = 'zh'): 
    for word in words:  
        salt = random.randint(32768, 65536)
        sign = appid + word + str(salt) + secretKey
        myMd5 = hashlib.md5()
        myMd5.update(sign.encode("utf-8"))
        sign = myMd5.hexdigest()
        yield '/api/trans/vip/translate'+'?appid='+appid+'&q='+quote(word)+'&from='+fromLang+'&to='+toLang+'&salt='+str(salt)+'&sign='+sign

def get_translate_word(url):
    try:
        response = requests.get('http://api.fanyi.baidu.com' + url)
        result=response.json()
        for item in result['trans_result']:
            text_1 = colored(item['src']+':', "red")
            text_2 = colored(item['dst'], "green")
            print(text_1+text_2)
    except Exception as e:
        print(e)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], ["help"])
        #获取命令行输入
    except getopt.GetoptError :
        pass

    match = re.findall(r'[\w.]+', " ".join(args).lower())
    word = " ".join(match)
    words = word.split( )
    for u in get_myurl(words):
        get_translate_word(u)
        time.sleep(1)

if __name__ == '__main__':
    main()
