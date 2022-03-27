import datetime
import logging
import sys
import time
from logging.handlers import RotatingFileHandler

class jjlogger:
    def __init__(self, appName, fileLocation=None):
        self.logger = logging.getLogger(appName)
        self.logger.setLevel(logging.INFO)
        logging.Formatter.converter = time.gmtime

        maxSize = 1024 * 1024 * 20
        formatter = logging.Formatter(
            f"{{ 'time':'%(asctime)s.%(msecs)03dZ'"
            f",'name':'%(name)s'"
            f",'level':'%(levelname)s'"
            f",'message':'%(message)s' }}",
            datefmt='%Y-%m-%dT%H:%M:%S')

        # add a handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        if fileLocation is not None:
            handler = RotatingFileHandler(fileLocation, maxBytes=maxSize, backupCount=10)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info("log start")
    def getLogger(self):
        return self.logger
