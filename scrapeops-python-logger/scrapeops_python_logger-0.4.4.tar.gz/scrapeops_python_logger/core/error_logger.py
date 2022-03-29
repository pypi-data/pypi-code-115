import json
import logging
import sys

from scrapeops_python_logger.stats.model import OverallStatsModel, PeriodicStatsModel 
from scrapeops_python_logger.utils import utils


         
class TailLogger(object):

    def __init__(self):
        self._log_dict = {}
        self._log_handler = TailLogHandler(self._log_dict)

    def contents(self):
        jsonLogs = json.dumps(self._log_dict, indent= 2)

        self._log_handler.flush()

        return jsonLogs

    @property
    def log_handler(self):
        return self._log_handler




class TailLogHandler(logging.Handler):

    retryErrors = [
        "Couldn't bind",
        "Hostname couldn't be looked up'"
        "No route to host",
        "Connection was refused by other side",
        "TCP connection timed out",
        "File used for UNIX socket is no good",
        "Service name given as port is unknown",
        "User aborted connection",
        "User timeout caused connection failure",
        "An SSL error occurred",
        "Could not verify something that was supposed to be signed.",
        "The peer rejected our verify error.",
        "We did not find a certificate where we expected to find one.",
        "Bad Request",
        "Unauthorized",
        "Payment Required",
        "Forbidden",
        "Not Found",
        "Method Not Allowed",
        "Request Time-out",
        "Internal Server Error",
        "Bad Gateway",
        "Service Unavailable",
        "HTTP Version not supported",
        "Gateway Time-out",
        "Unknown Status",
    ]

    def __init__(self, log_dict):
        logging.Handler.__init__(self)
        self.log_dict = log_dict


    def flush(self):
        self.log_dict.clear()


    def emit(self, record):

        try:
           
            if(record.levelname == "ERROR" or record.levelname == "WARNING" or record.levelname == "CRITICAL"):

                if record.levelname == "ERROR":
                    OverallStatsModel._overall_errors = OverallStatsModel._overall_errors + 1 
                    OverallStatsModel._overall_stats['log_count/ERROR'] = OverallStatsModel._overall_errors

                    PeriodicStatsModel._periodic_stats['log_count/ERROR'] = PeriodicStatsModel._periodic_errors + 1

                elif record.levelname == "CRITICAL": 
                    OverallStatsModel._overall_criticals = OverallStatsModel._overall_criticals + 1 
                    OverallStatsModel._overall_stats['log_count/CRITICAL'] = OverallStatsModel._overall_criticals

                    PeriodicStatsModel._periodic_stats['log_count/CRITICAL'] = PeriodicStatsModel._periodic_criticals + 1

                else: 

                    OverallStatsModel._overall_warnings = OverallStatsModel._overall_warnings + 1 
                    OverallStatsModel._overall_stats['log_count/WARNING'] = OverallStatsModel._overall_warnings

                    PeriodicStatsModel._periodic_stats['log_count/WARNING'] = PeriodicStatsModel._periodic_warnings + 1



                errorMessage = record.message
                fileAndLine = record.pathname + ', line: ' + str(record.lineno)
                dateTime = "" #record.asctime
                type = record.levelname
                engine = record.name


                #covering warnings/probableCause/traceback missing
                traceback = 'No traceback available'
                probableCause = ''

                if record.exc_text is not None:
                    traceback = record.exc_text
                    splitTraceback = traceback.split('\n')
                    probableCause = splitTraceback[len(splitTraceback) - 1]


                #covering retrys
                if("Gave up retrying <GET" in record.message):

                    for retryError in self.retryErrors:
                        if(retryError in record.message):
                            
                            errorMessage = "Error: Gave up retrying GET request - " + retryError
                            fileAndLine = ''
                            probableCause = retryError
                            break

                
                if errorMessage in self.log_dict:
                    self.log_dict[errorMessage]['count'] = self.log_dict[errorMessage]['count'] + 1
                else:
                    self.log_dict[errorMessage] = {
                        'type': type,
                        'engine': engine,
                        'name': errorMessage,
                        'count': 1, 
                        'traceback': traceback, 
                        'message' : probableCause, 
                        'filepath': fileAndLine, 
                        'dateTime': dateTime
                        }

                        
        except Exception as e:
            logging.info('Error: Error in error logger')
            logging.info(e, exc_info=True)




def except_hook(type, value, tback):
    # manage unhandled exception here
    logging.error(value, exc_info = True)
    # then call the default handler
    sys.__excepthook__(type, value, tback) 

sys.excepthook = except_hook