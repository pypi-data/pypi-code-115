# -*- encoding: utf-8 -*-
# @Author: haogooder
# @Date:
# @Description:
import logging as _log


class LogUtil(object):
    _level = _log.INFO

    _log_dict = {}

    @staticmethod
    def get_logger(name):
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError()
        logger = _log.getLogger(name)
        if LogUtil._log_dict.get(name) is None:
            LogUtil._log_dict[name] = logger
        else:
            return LogUtil._log_dict.get(name)
        logger.setLevel(LogUtil._level)
        fh = _log.Formatter('%(asctime)s[%(levelname)9s] %(name)-16s | %(lineno)4s: %(filename)-20s | %(message)s')
        sh = _log.StreamHandler()
        sh.setFormatter(fh)
        logger.addHandler(sh)
        logger.propagate = False
        return logger


if __name__ == "__main__":
    pass
