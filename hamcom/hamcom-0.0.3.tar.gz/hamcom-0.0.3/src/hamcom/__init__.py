import socket
import msgpack
import threading
import time as t
import os
import sys

TIMEOUT = 10
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!D"
FORWARD_MESSAGE = "!F"
TURN_MESSAGE = "!T"
CHECK_MESSAGE = "!C"
IPADD = "127.0.0.1"
PORT = 5050

def setIP(newip):
    global IPADD 
    IPADD = newip

def setTIMEOUT(newtimeout):
    global TIMEOUT
    TIMEOUT = newtimeout

if sys.version_info < (3, 6):
    print("Python version 3.6 or higher required!")
    quit()      

class Pc():
    def __init__(self, ip, port):
        self.__address = (ip, port)
        self.__message = ""
        self.__connection_status = "no connection"

    def establish_connection(self):
        while True:
            try:
                self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__sock.settimeout(TIMEOUT)
                self.__sock.connect(self.__address)
                self.__connection_status = "connection established"
                return 0
            except socket.timeout:
                print("Cannot connect to [{}], timed out".format(self.__address))
                return 1
            except ConnectionRefusedError:
                self.__connection_status = "connection refused"
                print("connection refused, trying again in 5 seconds")
                t.sleep(5)
                continue
            
    
    def send_msg(self, msg):
        if self.establish_connection(): return -1
        message = msg.encode(FORMAT)
        try: 
            self.__sock.send(message)
            answer = self.__sock.recv(4096).decode(FORMAT)
            self.__sock.close()
            self.__connection_status = "connection closed"
            return answer
        except ConnectionResetError:
            print("connection reset, trying to reconnect")
            self.send_msg(msg)
        except socket.timeout:
            print("socket timed out, hamster not responding, check manually and restart")
            quit()
            
    def forward(self):
        return self.send_msg(FORWARD_MESSAGE)

    def turn(self):
        return self.send_msg(TURN_MESSAGE)

    def disconnect(self):
        return self.send_msg(DISCONNECT_MESSAGE)

    def check_front(self):
        return self.send_msg(CHECK_MESSAGE)
    


def vor():
    return Pc(IPADD, PORT).forward()

def linksUm():
    return Pc(IPADD, PORT).turn()

def vornFrei():
    return Pc(IPADD, PORT).check_front() 

def ausschalten():
    return Pc(IPADD, PORT).disconnect()

if __name__ == "__main__":
    while 1:
        print("while 1")
        try:
            vor()
            print("forward sent")
                
            linksUm()
            print("turn sent")
                
        except ConnectionRefusedError:
            print("some error occured, trying again")
            t.sleep(1)
            pass