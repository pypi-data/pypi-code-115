#coding=utf-8
'''
Operations relates to network
'''
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def get_public_ip(url = 'http://pv.sohu.com/cityjson?ie=utf-8'):
    try:
        req = requests.post(url)
        return req.text.split('"')[3]
    except Exception as e:
        return e
    
def send_email_qq(qq_num,pwd,str_msg,str_title):
    '''send email to itself via qq mail'''
    try:
        msg_from = str(qq_num) + '@qq.com'
        to= [msg_from] 
        conntent=str_msg
        msg = MIMEMultipart()
        msg.attach(MIMEText(conntent,'plain','utf-8'))
        msg['Subject']=str_title
        msg['From']=msg_from
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(msg_from, pwd)
        s.sendmail(msg_from,to,msg.as_string())
        return True
    except Exception as e:
        print(e)
        return False

def send_public_ip_to_me(qq_num,pwd):
    ip_str = get_public_ip()
    send_email_qq(qq_num,pwd,ip_str+'\r','Auto-IP-Address Push')