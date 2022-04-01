from ._internal import RootCommand


class Python(RootCommand):
    __name__ = "python3"
    globals = globals()

    def set_params(self):
        # -m mod : run library module as a script (terminates option list)
        self.add_param("-m",
                       help_text="以脚本的方式运行指定模块")


python = Python()