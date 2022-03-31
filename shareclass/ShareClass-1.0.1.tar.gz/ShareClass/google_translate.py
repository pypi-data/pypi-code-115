# ======================
# -*- coding:utf-8 -*-
# @author:Beall
# @time  :2021/11/18 13:54
# @file  :python 接口发布.py
# ======================
import re
import html
from urllib import parse
import requests

GOOGLE_TRANSLATE_URL = 'http://translate.google.cn/m?q=%s&tl=%s&sl=%s'
translate_dict = {
    'afrikaans': 'af',
    'arabic': 'ar',
    'belarusian': 'be',
    'bulgarian': 'bg',
    'catalan': 'ca',
    'czech': 'cs',
    'welsh': 'cy',
    'danish': 'da',
    'german': 'de',
    'greek': 'el',
    'english': 'en',
    'esperanto': 'eo',
    'spanish': 'es',
    'estonian': 'et',
    'persian': 'fa',
    'finnish': 'fi',
    'french': 'fr',
    'irish': 'ga',
    'galician': 'gl',
    'hindi': 'hi',
    'croatian': 'hr',
    'hungarian': 'hu',
    'indonesian': 'id',
    'icelandic': 'is',
    'italian': 'it',
    'hebrew': 'iw',
    'japanese': 'ja',
    'korean': 'ko',
    'latin': 'la',
    'lithuanian': 'lt',
    'latvian': 'lv',
    'macedonian': 'mk',
    'malay': 'ms',
    'maltese': 'mt',
    'dutch': 'nl',
    'norwegian': 'no',
    'polish': 'pl',
    'portuguese': 'pt',
    'romanian': 'ro',
    'russian': 'ru',
    'slovak': 'sk',
    'slovenian': 'sl',
    'albanian': 'sq',
    'serbian': 'sr',
    'swedish': 'sv',
    'swahili': 'sw',
    'thai': 'th',
    'filipino': 'tl',
    'turkish': 'tr',
    'ukrainian': 'uk',
    'vietnamese': 'vi',
    'yiddish': 'yi',
    'chinese_simplified': 'zh-CN',
    'chinese_traditional': 'zh-TW',
    'auto': 'auto'
}


def translate(lan_From, lan_To, text):
    text = parse.quote(text)
    url = GOOGLE_TRANSLATE_URL % (text, lan_To, lan_From)
    response = requests.get(url)
    data = response.text
    expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
    result = re.findall(expr, data)
    if (len(result) == 0):
        return ""

    return html.unescape(result[0])


if __name__ == "__main__":
    text = '''面料名称:蕾丝
是否支持贴牌:不支持
是否支持代工:支持
主面料成分:锦纶/尼龙
主面料成分的含量:90（%）
里料成分:棉
里料成分含量:32.8（%）
款式:超薄型
适用人群:青年女性
风格:性感妩媚
是否无缝:否
是否有钢圈:软钢圈
设计特色:蝴蝶结,提花,蕾丝边
罩杯型:3/4罩杯
模杯类型:超薄模杯
肩带类型:固定双肩带
排扣类型:后双排搭扣
误差范围:0.1-0.2cm
适合季节:夏季,冬季,春季,秋季
是否外贸:是
库存类型:整单
生产周期:45天
质量等级:一等品
是否进口:否
功能:聚拢，透气，大胸显小
主要下游平台:wish,速卖通,独立站,LAZADA,其他'''
    print(translate(lan_From="auto", lan_To="en", text=text))
