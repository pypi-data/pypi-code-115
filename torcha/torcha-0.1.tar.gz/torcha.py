#!/usr/bin/env python  
# Copyright (c) 2022-2023 Papa Crouz
# Distributed under the MIT/X11 software license, see the accompanying
# file license http://www.opensource.org/licenses/mit-license.php.


from stem.control import Controller
from stem.connection import *
from stem import Signal
import threading
import requests
import socket 
import socks
import sys


# local 
import context as ctx


class ExitedThread(threading.Thread):
    def __init__(self):
        super(ExitedThread, self).__init__()
        self.exit = False


    def run(self):
        while True:
            if self.exit:
                break 
            self.start_()



class TorThread(ExitedThread):
    def __init__(self, tor_controller=None):
        super(TorThread, self).__init__()
        self.controller = None
        self.controllerError = ''
        self.lastknowip = self.get_current_ip()

        print ("TorThread started")


        if not tor_controller:
                ret = self.controller_()
                if not ret:
                    print('TorThread stoped - Error() - ' + str(self.controllerError) + ' is tor runnig ?.')
                    sys.exit(1)
        else:
            self.controller = tor_controller
            try:
                version = controller.get_version()
            except Exception as e:
                print('TorThread - Exits. Controller needs to be authenticated.')
                sys.exit(1)


        # Redirects all TCP traffic over Tor 
        socks.setdefaultproxy(socks.SOCKS5, '127.0.0.1', 9050)
        socket.socket = socks.socksocket


       



    def start_(self):
        while True: 
            if self.exit:
                break



            # Torca is a pure thread that use stem, Stem is a Python controller library for Tor, 
            # with Stem you can use Tor's control protocol to script against the Tor process.

            # The job of this thread is to use Stem in order Automatically switch to new to clean circuits, 
            # it basically trying to establishes a new "clean" pathway through the Tor network continually 
            # Essentially the reason of switching to new clean circuits is to avoid the previous set of 
            # proxies you were using do not see the "to/from" points of your new connections, new circuits new IP.



             
            # If stem loose connection with tor protocol, exit. There is no reason to running as said above 
            # The job of this thread is to use Stem in order Automatically switch to new to clean circuits,  
            if not self.controller.is_alive():
                print('TorThreadHandler() - Controller disconnected from tor, is tor running ?')
                sys.exit(1) 


            # Check whenever tor would currently accept a NEWNYM signal, and send a newnym signal, witch 
            # will make Tor switch to clean circuits, so new application requests don't share any circuits with old ones. 
            if self.controller.is_newnym_available():
                self.controller.signal(Signal.NEWNYM)
                ret = self.get_current_ip()
                if self.lastknowip != ret:    
                    self.lastknowip = ret
   



    def _reset(self):
        # reset socks to defaults
        socks.setdefaultproxy(None)
        socket.socket = socks.socksocket



    def controller_(self):
        try:
            self.controller = Controller.from_port()
            self.controller.authenticate()
        except Exception as e:
            self.controllerError = e 
            return False
         
        return True


    def verify_tor_connection(self):
        content = requests.get('https://check.torproject.org/').text
        # <h1 class="off">  - not using tor
        # <h1 class="not">  - using tor without torbrowser
        # <h1 class="on">  - using tor with torbrowser
        return content.find('class="off"')==-1


    def get_current_ip(self):
        try:
            r = requests.get('http://httpbin.org/ip')
        except Exception as e:
            print (str(e))
        else:
            return r.json()['origin']





def startTor(controller=None):

    if ctx.fTorThreadRunning is False:
        ctx.fTorThreadRunning = TorThread(None)
        ctx.fTorThreadRunning.start()
        if not ctx.fTorThreadRunning.verify_tor_connection():
            print("Can't verify tor connection, exiting..")
            sys.exit(1)
    return True 


def stopTor():

    if ctx.fTorThreadRunning is not None:
        ctx.fTorThreadRunning._reset()
        ctx.fTorThreadRunning.exit = True
        ctx.fTorThreadRunning = None
        return True 
    return False



