# ======================
# -*- coding:utf-8 -*-
# @author:Beall
# @time  :2022/3/23 14:43
# @file  :exchange_rate.py
# ======================
import requests
from bs4 import BeautifulSoup


def exchange_rate(form_currency, to_currency="USD", num=1):
    """
    汇率换算
    :param form_currency: 需要转化的币种
    :param to_currency: 待转化的币种, 默认USD(美元)
    :param num: 需要转化的钱, 默认为1
    :return: 实时汇率
    """
    print(f'正在查询{form_currency} => {to_currency}汇率...')
    for i in range(3):
        try:
            header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/89.0.4389.90 Safari/537.36',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/'
                          '*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Host': 'qq.ip138.com'}
            url = f"https://qq.ip138.com/hl.asp?from={form_currency}&to={to_currency}&q={num}"
            web = requests.get(url, headers=header)
            if web.status_code == 200:
                soup = BeautifulSoup(web.text, 'html.parser')
                result = float([i.get_text() for i in soup.find_all("td")][-1])
                print(f'查询成功, {num} {form_currency} = {result} {to_currency}')
                return result
                break
            else:
                raise Exception
        except Exception as e:
            print(f'出错:{e}, url: {url}, 重试次数:{i + 1}')
        if i == 2:
            print('三次重试均失败！')


if __name__ == '__main__':
    exchange_rate('CNY')
