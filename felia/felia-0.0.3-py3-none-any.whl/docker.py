from ._internal import SubCommand, RootCommand, config

__all__ = ["docker",
           ]


class Ps(SubCommand):
    __name__ = "ps"

    def set_params(self):
        self.add_param("--all", "显示所有容器", "-a")
        self.add_param("--quiet", "只显示容器ID", "-q")


class Rm(SubCommand):
    __name__ = "rm"


class Rmi(SubCommand):
    """移除一个或者多个镜像"""
    __name__ = "rmi"


class Diff(SubCommand):
    """显示了镜像被实例化成一个容器以来哪些文件受到了影响

    https://docs.docker.com/engine/reference/commandline/diff/
    """
    __name__ = "diff"


class Run(SubCommand):
    """以容器形式运行一个Docker镜像

    源码: https://github.com/docker/compose/blob/v2/cmd/compose/run.go
    """
    __name__ = "run"

    def set_params(self):
        self.add_param("--interactive",
                       help_text="保持STDIN打开, 用于控制台交互",
                       short="-i")
        self.add_param("--tty",
                       help_text="分配TTY设备, 可以支持终端登录",
                       short="-t")
        self.add_param("--publish",
                       help_text="指定容器包路的端口",
                       short="-p")
        self.add_param("--name",
                       help_text="分配容器的名称")
        self.add_param("--detach",
                       help_text="在后台运行容器和打印容器id",
                       short="-d")

        self.add_param("--label",
                       help_text="设置LABEL元数据",
                       short="-l")

        self.add_param("--volume",
                       help_text="挂载卷, 格式 本地目录:远程目录",
                       short="-v")

        # ============= 以下参数不常用 =============================

        __policy = """no:容器退出时不重启;\nalways:容器退出时总是重启;\nunless-stopped:总是重启, 不过显示停止除外\non-failure[:max-retry]:只在失败时重启"""
        self.add_param("--restart",
                       help_text=f"设置重启策略, 默认值'no'。策略:\n{__policy}")

        # Docker实践(第2版) 技巧37
        self.add_param("--volumes-from",
                       help_text="挂载指定的数据容器")


class Tag(SubCommand):
    """给一个Docker镜像打标签"""
    __name__ = "tag"


class Stop(SubCommand):
    """干净地终结容器"""
    __name__ = "stop"


class Logs(SubCommand):
    """抓取容器的日志

    源码: https://github.com/docker/compose/blob/v2/cmd/compose/logs.go
    """
    __name__ = "logs"


class Exec(SubCommand):
    """在容器执行bash命令"""
    __name__ = "exec"


class Build(SubCommand):
    """构建一个Docker镜像

    文档: https://docs.docker.com/engine/reference/commandline/build/
    """
    __name__ = "build"

    def set_params(self):
        self.add_param("--tag",
                       help_text="打标签, 格式: 'name:tag'",
                       short="-t")
        self.add_param("--build-arg",
                       help_text="设置运行时的变量值(ARG)")

        # ======== 以下参数不常用 ========================
        self.add_param("--no-cache",
                       help_text="构建时不使用缓存")


class Images(SubCommand):
    """列出所有镜像"""
    __name__ = "images"


class Restart(SubCommand):
    """重启一个或多个容器"""
    __name__ = "restart"


class Version(SubCommand):
    __name__ = "version"


class Start(SubCommand):
    """启动一个或多个停止状态的容器"""
    __name__ = "start"


class Commit(SubCommand):
    """将一个Docker容器作为一个镜像提交"""
    __name__ = "commit"


class Docker(RootCommand):
    __name__ = 'docker'
    globals = globals()
    subcommands = [
            Ps,
            Rm,
            Rmi,
            Run,
            Tag,
            Stop,
            Diff,
            Logs,
            Exec,
            Build,
            Start,
            Images,
            Commit,
            Restart,
            Version,
        ]

    # def chdir(self):
    #     """TODO 读取配置文件获取所有可切换的路径"""
    #     config["DOCKER"]

    def change_conn(self):
        """

        :return:
        """
        section = config[self.__class__.__name__.upper()]
        import logging
        logger = logging.getLogger(__name__)
        projects = list(section.items())
        if len(projects) == 0:
            return

        print(1, "Local")
        for index, value in enumerate(projects, start=2):
            print(index, value[0])
        i = int(input("请选择一个项目"))

        if i == 1:
            import sys
            if sys.platform == "win32" and len(self.pre) == 0:
                self.pre.append('powershell.exe')
                self.pre.append('wsl')
            return

        from fabric import Connection
        import json
        logger.debug(f"projects: {projects}")
        conf = json.loads(projects[i - 2][1])
        conn = Connection(conf["host"],
                          user=conf["user"],
                          port=conf["port"],
                          connect_kwargs={"key_filename": conf["key_filename"]})
        self.pre.clear()
        self.run = conn.sudo


@Docker.subcommand
class Pull(SubCommand):
    """拉取镜像

    https://docs.docker.com/engine/reference/commandline/pull/
    """
    __name__ = "pull"


@Docker.subcommand
class Search(SubCommand):
    """检索Docker Hub镜像

    Docker实践(第2版) 第95页
    """
    __name__ = "search"


@Docker.subcommand
class Inspect(SubCommand):
    """显示容器的信息

    Return low-level information on Docker objects

    Docker实践(第2版) 技巧30

    https://docs.docker.com/engine/reference/commandline/inspect/
    """
    __name__ = "inspect"

    def set_params(self):
        # 使用format标志的例子: https://docs.docker.com/engine/reference/commandline/inspect/#examples
        self.add_param("--format",
                       help_text="使用Go模板格式化输出",
                       short="-f")

    def get_instance_IP_address(self, obj):
        """https://docs.docker.com/engine/reference/commandline/inspect/#get-an-instances-ip-address

        单个使用{{.NetworkSettings.IPAddress}}
        """
        self.format("'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'")(obj)

    def get_instance_MAC_address(self, obj):
        """https://docs.docker.com/engine/reference/commandline/inspect/#get-an-instances-mac-address"""

    def get_instance_log_path(self, obj):
        """https://docs.docker.com/engine/reference/commandline/inspect/#get-an-instances-log-path"""
        self.format("'{{.LogPath}}'")(obj)

    def get_instance_image_name(self, obj):
        """https://docs.docker.com/engine/reference/commandline/inspect/#get-an-instances-image-name"""
        self.format("'{{.Config.Image}}'")(obj)

    def list_all_port_bindings(self, obj):
        """https://docs.docker.com/engine/reference/commandline/inspect/#list-all-port-bindings"""
        self.format("'{{range $p, $conf := .NetworkSettings.Ports}} {{$p}} -> {{(index $conf 0).HostPort}} {{end}}'")(obj)

    def get_subsection_in_JSON_format(self, obj):
        """https://docs.docker.com/engine/reference/commandline/inspect/#get-a-subsection-in-json-format"""
        self.format("'{{json .Config}}'")(obj)


docker = Docker()
# change_conn(docker, config["DOCKER"])
