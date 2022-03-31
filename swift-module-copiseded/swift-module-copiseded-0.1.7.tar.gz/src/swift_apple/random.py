import random
def randomInt_Float(fromInt,toInt):
    randomnum = random.unifrom(fromInt,toInt)
    return randomnum
def randomInt_Integers(fromInt,toInt):
    randomnumber = random.randint(fromInt,toInt)
    return randomnumber
def randomInt_type_MaxMinNumber():
    global list_max
    global list_min
    global list_1
    #使用循环取值支持输入，并检测异常，冒泡输入8位
    list_1 = list()
    try:
        for i in range(8):
            num = eval(input('请输入数字'))
            list_1.append(num)
        print(list_1)
        c = list_1[0]
        for i in list_1:
            if c!=i:
                if c<i:
                    c=i
                    list_max=i
        for b in list_1:
            if b!=c:
                if c>b:
                    c=b
                    list_min=c
        print(list_max)
        print(list_min)
    except Exception as e:
        print(e)
