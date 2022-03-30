import time
import sys
import logging
import logging.handlers
name = "HandyLib"


def get_logger(level='info', test_flag=False,
               filename='',
               maxsize=1024*1024*3,
               backup_num=5, encoding='utf-8'
               ):
    '''
    ruturns a logger, 
    if test_flag is True or level is set to logging.DEBUG,
    it will output to terminal
    '''
    level = level.upper()
    if level == 'INFO':
        level = logging.INFO
    elif level == 'WARNING' or level == 'WARN':
        level = logging.WARNING
    elif level == 'ERROR' or level == 'ERR':
        level = logging.ERROR
    elif level == 'DEBUG':
        level = logging.DEBUG
    else:
        print('unknown logging level:{level}')
    if filename == '':
        temp = sys.argv[0].split('.')
        temp = temp[:-1]
        filename = '.'.join(temp) + '.log'

    logger = logging.getLogger()
    format = logging.Formatter(
        "\n%(levelname)s - line:%(lineno)d - %(filename)s = %(asctime)s\n[ %(message)s ]")    # output format

    handler = logging.handlers.RotatingFileHandler(
        filename, maxBytes=maxsize, backupCount=backup_num, encoding=encoding)
    handler.setFormatter(format)
    logger.addHandler(handler)
    if test_flag or level == logging.DEBUG:
        # output to standard output
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setFormatter(format)
        logger.addHandler(sh)
    logger.setLevel(level)
    return logger


def time_this(fn):
    def wrap(*args, **kwargs):
        start = time.time()
        fn(*args, **kwargs)
        print('[{0}] took {1:.10f} seconds'.format(
            fn.__name__, time.time() - start))
    return wrap
