import os
import sys
import logging
from subprocess import run
from pathlib import Path
from importlib import import_module
import warnings

from fabric import Result
import win32api

from .configuration import ConfMixin

logger = logging.getLogger(__name__)
h = logging.StreamHandler()
h.setFormatter(logging.Formatter("%(levelname)s $ %(message)s"))
logger.addHandler(h)
logger.setLevel(logging.INFO)


class BaseCommand:
    """
    cli.para1().para2()(run=False) # 只输出命令，不执行
    等价于
    cli --para1 --para2
    """

    def __init__(self):
        self._params = []
        self.pre = []
        self.args = []
        self.cmd = [self.__name__]
        self.run = run
        self.setup()

    def add_param(self, param, help_text=None, short=None, default=None):
        self._params.append(Param(param, help_text, short, default))

    def set_params(self):
        pass

    def setup(self):
        if sys.platform == "win32":
            self.pre.append('powershell.exe')
            self.pre.append('wsl')

        self.set_params()

        _self = self
        for obj in self._params:
            attr_name = obj.option.replace("-", "")

            class Func:
                def __init__(self):
                    self.option = obj.option
                    self.default = obj.default

                def __call__(self, value=None):
                    option = self.option
                    v = value or self.default
                    logger.debug(v)
                    if v:
                        option += " " + v

                    if option not in _self.args:
                        _self.args.append(option)

                    return _self

                def __str__(self):
                    return ' '.join(_self.cmd + _self.args)

                def __repr__(self):
                    return ' '.join(_self.cmd + _self.args)

            setattr(self, attr_name, Func())

    def __call__(self, *args, **kwargs):
        pass

    def show_commands(self):
        self(run=False)

    def help(self):
        print(f"Usage:  {self.cmd[0]}")
        print()
        for obj in self._params:
            obj.print_help()

    def clear_args(self):
        self.args.clear()


class RootCommand(BaseCommand, ConfMixin):
    subcommands: list
    globals: dict

    def setup(self):
        super(RootCommand, self).setup()
        if not hasattr(self, 'subcommands'):
            return

        while self.subcommands:
            CMD = self.subcommands.pop()
            obj = CMD(self)
            setattr(self, CMD.__name__, obj)
            obj_name = f"{self.__name__}_{CMD.__name__}".lower()
            self.globals.setdefault(obj_name,
                                    obj)

            if _all := self.globals.get("__all__"):
                _all.append(obj_name)

    def __call__(self, *args, run=True):
        _args = self.args + list(args)
        cmd = self.cmd + _args
        logger.info(" ".join(cmd))
        if run:
            if hasattr(self, '__main__'):
                module_name, func_name = getattr(self, '__main__').rsplit(".", 1)
                return getattr(import_module(module_name), func_name)(args)
            elif hasattr(self, "use_shell") and getattr(self, "use_shell"):
                # Pycharm python console遇到input会卡住不能交互, 用win32api调用powershell窗口处理
                return win32api.ShellExecute(0, "open", "powershell.exe", " ".join(cmd), "", 1)
            else:
                content = " ".join(self.pre + cmd)
                if self.pre:
                    content = content.replace(" | ", " | wsl ")
                return self.run(content)

    @classmethod
    def subcommand(cls, sub_class):
        if not hasattr(cls, 'subcommands'):
            setattr(cls, 'subcommands', [])
        cls.subcommands.append(sub_class)
        del sub_class


class SubCommand(BaseCommand):

    def __init__(self, root):
        super(SubCommand, self).__init__()
        self.root = root

    def __call__(self, *args, run=True):
        _args = self.args + list(args)
        cmd = self.cmd + _args
        name = f'{self.__name__}{"_".join(_args)}'.replace("-", "_")

        class Func:
            """定义全局方法"""
            @staticmethod
            def execute():
                return self.root(' '.join(cmd))

            def __repr__(self):
                return ' '.join(cmd)

        func = Func()

        result = self.root(*cmd, run=run)
        if run:
            self.clear_args()
            self.root.clear_args()

            if isinstance(result, Result):
                returncode = getattr(result, "exited")
            else:
                returncode = getattr(result, 'returncode')

            if not hasattr(self.root, name) and returncode == 0:
                self.root.globals.setdefault(f"{self.root.__name__}_{name}", func)
                setattr(self.root, f'{name}', func)


class Param:
    def __init__(self, option, help_text, short=None, default=None):
        self.option = option
        self.help_text = help_text
        self.short = short
        self.default = default

    def print_help(self):
        print(self.short or "  ", self.option, self.help_text)


def change_path(projects: list[tuple[str, Path]]):
    if len(projects) == 1:
        path = projects[0][1]
    else:
        for index, value in enumerate(projects):
            print(index + 1, value[0])

        i = int(input("请选择一个项目")) - 1
        path = projects[i][1]

    print("切换路径:", path)
    os.chdir(path)


def change_workdir(section):
    projects = list(section.items())

    if len(projects) == 1:
        path = projects[0][1]
    else:
        for index, value in enumerate(projects):
            print(index + 1, value[0])

        i = int(input("请选择一个项目")) - 1
        path = projects[i][1]

    print("切换路径:", path)
    os.chdir(path)


def change_conn(docker, section):
    warnings.warn("弃用, 请使用RootCommand下的change_conn", DeprecationWarning)
    projects = list(section.items())
    if len(projects) == 0:
        return

    print(1, "Local")
    for index, value in enumerate(projects, start=2):
        print(index, value[0])
    i = int(input("请选择一个项目"))

    if i == 1:
        return
    from fabric import Connection
    import json
    logger.debug(f"projects: {projects}")
    config = json.loads(projects[i - 2][1])
    conn = Connection(config["host"],
                      user=config["user"],
                      port=config["port"],
                      connect_kwargs={"key_filename": config["key_filename"]})

    docker.run = conn.sudo
