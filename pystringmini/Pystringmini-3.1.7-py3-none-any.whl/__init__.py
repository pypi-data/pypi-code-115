#Requirement
def String(ls):
    st=''
    for i in ls:
        st=st+str(i)
    return st

def List(string1):
    ls=[]
    for i in string1:
        ls.append(i)
    return ls

#to conver given string is uppercase
def Lowercase(string):
    ls=[]
    for i in string:
        #print(i)
        if ord(i)>=97 and ord(i)<=122:
            ls.append(i)
        elif ord(i)>=65 and ord(i)<=90: #caps
            temp=ord(i)+32
            ls.append(chr(temp))
        else:
            ls.append(i)
    return String(ls)

#to conver given string is lowercase
def Uppercase(string):
    ls=[]
    for i in string:
        #print(i)
        if ord(i)>=97 and ord(i)<=122:
            temp=ord(i)-32
            ls.append(chr(temp))
        elif ord(i)>=65 and ord(i)<=90: #caps
            ls.append(i)
        else:
            ls.append(i)
    return String(ls)

#capitalize
def Capitalize(string):
    ls=''
    temp=string[0].upper()
    ls=ls+temp
    for i in range(1,len(string)):
        ls=ls+string[i]
    return String(ls)

#length
def Length(string):
    cnt=0
    for i in string:
        cnt=cnt+1
    return cnt

#given string digit or not
def Digit(string):
    cnt=0
    for i in string:
        if ord(i)>48 and ord(i)<57:
            cnt=cnt+1
    if cnt==len(string):
        return True
    else:
        return False

#minimum character in given string
def Minimum(string):
    cnt=[]
    for i in string.strip():
        if ord(i)>=97 and ord(i)<=122:
            temp=int(ord(i))
            cnt.append(temp)
        elif ord(i)>=65 and ord(i)<=90: #caps
            temp=int(ord(i))
            cnt.append(temp)
        else:
            continue
    cnt.sort()
    return chr(cnt[0])

#maximum character in given string
def Maximum(string):
    cnt=[]
    for i in string.strip():
        if ord(i)>=97 and ord(i)<=122:
            temp=int(ord(i))
            cnt.append(temp)
        elif ord(i)>=65 and ord(i)<=90: #caps
            temp=int(ord(i))
            cnt.append(temp)
        else:
            continue
    cnt.sort()
    return chr(cnt[len(cnt)-1])

#replace the given word in the string
def Replace(string,original_word,replace_word):
    ls=string.split()
    temp=''
    for i in range(0,len(ls)):
        if ls[i]==original_word:
            ls[i]=replace_word
    for i in range(0,len(ls)):
        temp=temp+ls[i]
        temp=temp+" "
    return temp 

#encryption string
def Encryption(string):
    ls=[]
    for i in string:
        if i!=' ':
            if ord(i)>=65 and ord(i)<=87:
                ls.append(chr(ord(i)+3))
            elif ord(i)>=97 and ord(i)<=119:
                ls.append(chr(ord(i)+3))
            else:
                if ord(i)==88:
                    ls.append(chr(65))
                elif ord(i)==89:
                    ls.append(chr(66))
                elif ord(i)==90:
                    ls.append(chr(67))
                elif ord(i)==120:
                    ls.append(chr(97))
                elif ord(i)==121:
                    ls.append(chr(98))
                elif ord(i)==122:
                    ls.append(chr(99))
                else:
                    ls.append(chr(ord(i)+3))
        else:
            ls.append(chr(ord(i)+3))
    return String(ls)


#decryption string
def Decryption(string):
    ls=[]
    for i in string:
        if i!=' ':
            if ord(i)>=69 and ord(i)<=90:
                ls.append(chr(ord(i)-3))
            elif ord(i)>=100 and ord(i)<=122:
                ls.append(chr(ord(i)-3))
            else:
                if ord(i)==65:
                    ls.append(chr(88))
                elif ord(i)==66:
                    ls.append(chr(89))
                elif ord(i)==67:
                    ls.append(chr(90))
                elif ord(i)==97:
                    ls.append(chr(120))
                elif ord(i)==98:
                    ls.append(chr(121))
                elif ord(i)==99:
                    ls.append(chr(122))
                else:
                    ls.append(chr(ord(i)-3))
        else:
            ls.append(chr(ord(i)-3))
    return String(ls)

#split
def Split(string):
    strtemp = ''
    string.strip()
    string=string+" "
    ls=[]
    for i in string:
        #print(i)
        if i!=' ':
            strtemp = strtemp+i
        else:
            ls.append(strtemp)
            strtemp=''
    return ls

#compare
def Compare(string1,string2):
    cnt=0
    ls1=List(string1)
    ls2=List(string2)
    for i in range(0,len(string1)):
        if ls1[i]==ls2[i]:
            cnt=cnt+1
        else:
            return False
    if cnt==len(string1):
        return True
    
#manual
def Help():
    return "https://pypi.org/project/Pystringmini/"

#contect
def About():
    return"Create by Thiyagarajan V \ntrj08012002@gmail.com \nThank You"
