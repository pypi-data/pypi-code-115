# ecoding=utf-8
import requests
from lxml import html

etree = html.etree

#判断设备是否接入网络
def isConnected():
    import requests
    try:
        html = requests.get("http://www.baidu.com", timeout=2)
    except:
        return False
    return True


def color(text, c_mod):
    if c_mod == "pink":
        return f"\033[0;35;40m{text}\033[0m"
    if c_mod == "red":
        return f"\033[0;31;40m{text}\033[0m"
    if c_mod == "yellow":
        return f"\033[0;33;40m{text}\033[0m"
    if c_mod == "blue":
        return f"\033[0;34;40m{text}\033[0m"
    if c_mod == "hotpink":
        return f"\033[0;35;40m{text}\033[0m"
    if c_mod == "purple":
        return f"\033[0;36;40m{text}\033[0m"
    if c_mod == "cream":
        return f"\033[0;37;40m{text}\033[0m"


def log(text, c_mod=None):
    import time
    if c_mod is not None:
        text = (str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + f":{text}"))
        textok=color(text, c_mod)
        return textok
    else:
        return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + f":{text}")


def split(text, s_mod, colora=False):
    if colora:
        text = f"\n\n\n\n\n\n- {text} -  {s_mod} :\n-------------------------\n"
        textok = color(text, s_mod)
        return(textok)
    else:
        return f"\n\n\n\n\n\n- {text} -  {s_mod}:\n--------------------------\n"


def help():

    textf = (
        "你是不是不知道怎么用的？那就让我来告诉你吧!!\n"
        "这个函数是一个输出工具的集合，是由鱼鱼有几斤整理的\n"
        "我整理了这几个项目\n"
        "---------------------\n"
        "1：spilt，它的作用就是弄出一个分割线，将无关的输出和自己想看到的分割线分割开来，这样就可以在一定层度上降低对头发的消耗啦\n"
        "2：logs，它的作用就是在前面加一个时间戳，主要是好看和装逼用的，但是用的好的话还是很可以的\n"
        "3：color，更改输出的颜色，目前支持的有：\n"
        "粉色，红色，米黄（yellow），蓝色，火粉（hotpink），紫色，淡黄（cream）)\n"
        " (注意哦,split和logs都是可以和color叠加使用的)\n"
        "---------------------\n"
        "split的语法是:\n"
        "logs.split(输出文字,s_mod='项目名')\n"
        "log的语法是:\n"
        "logs.log(输出文字)\n"
        "color的语法是:\n"
        "logs.color(输出文字)\n"
        "示例（可以这种方法套）"
        "print(logs.color(logs.split('帮助文档',s_mod='Fishconsole'),c_mod='blue'))\n"
        "---------------------\n"
        "Have a good time!祝你们玩的愉快（2022/3/29）")

    if isConnected():
        v = str(1.1111)
        url = "https://pypi.org/project/Fishconsole/"
        res = requests.get(url).text
        res_html = etree.HTML(res)
        # 从html对象中，用xpath来提取数据
        res_v = res_html.xpath("/html/body/main/div[2]/div/div[1]/h1/text()")[0]
        res_v=str(res_v[21:27])
        if res_v != v:
            updatainfo = split("警告", s_mod=f"Fishconsole {res_v}版本更新") + log(f"检测到最新版本号发生了变化，请在终端键入pip install --upgrade Fishconsole更新至最新版本")
            print(color(updatainfo, c_mod="red"))
            return textf
        else:
            return color(split("帮助文档",s_mod="Fishconsole")+textf,c_mod="cream")
    else:
        print(log("你的设备没有联网，请检查网络连接",c_mod="red"))
        return color(split("帮助文档", s_mod="Fishconsole") + textf, c_mod="hotpink")






