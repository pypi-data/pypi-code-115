from setuptools import setup, find_packages
import codecs
import os


VERSION = '0.0.1'
DESCRIPTION = 'Some things that will make my work easier'

# Setting up
setup(
    name="VFunctions",
    version=VERSION,
    author="sonkraft1",
    author_email="<skraft2727@gmail.com>",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=['shutil', 'os', 'tkinter', 'webbrowser', 'pygame' , 'pygame.camera' ,'selenium', 'webdriver_manager.chrome', 'time', 'smtplib', 'email.message', 'imghdr', 'playsound', 'google_drive_downloader', 'ctypes', 'socket', 'glob', 'geocoder', 'datetime', 'pathlib'],
    keywords=['python', 'video', 'stream', 'video stream', 'camera stream', 'sockets'],
    classifiers=[]
)