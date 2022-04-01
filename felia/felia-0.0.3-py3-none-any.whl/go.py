import logging

from felia._internal import SubCommand, RootCommand

logger = logging.getLogger('Golang')
h = logging.StreamHandler()
h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - | %(message)s"))
logger.addHandler(h)
logger.setLevel(logging.INFO)


class Mod(SubCommand):
    """项目和包管理"""
    subcmd = "mod"

    def set_params(self):
        self.add_param("init", help_text="在当前目录初始化")


class Go(RootCommand):
    __name__ = 'go'
    globals = globals()
    subcommands = [Mod, ]


go = Go()
go_mod = getattr(go, 'mod')
