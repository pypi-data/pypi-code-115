import logging

from felia._internal import RootCommand, change_workdir, config

logger = logging.getLogger('Golang')
h = logging.StreamHandler()
h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - | %(message)s"))
logger.addHandler(h)
logger.setLevel(logging.INFO)


class Protoc(RootCommand):
    """

    protoc --go_out=. --go_opt=paths=source_relative --go-grpc_out=. --go-grpc_opt=paths=source_relative browser.proto
    """
    __name__ = 'protoc'
    globals = globals()

    def set_params(self):
        self.add_param("--go_out",
                       help_text="指定pb文件所在生成目录")
        self.add_param("--go_opt",
                       help_text="固定值",
                       default="paths=source_relative")
        self.add_param("--go-grpc_out",
                       help_text="指定grpc pb文件所在生成目录")
        self.add_param("--go-grpc_opt",
                       help_text="固定值",
                       default="paths=source_relative")

    def script(self, run=True):
        """TODO 加装饰器断言项目"""
        self.go_out(".").go_opt().gogrpc_out(".").gogrpc_opt()("browser.proto", run=run)


protoc = Protoc()

change_workdir(config["PROTOC"])