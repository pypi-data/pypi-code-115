from ._internal import SubCommand, RootCommand

__all__ = ["pip"]


class Pip(RootCommand):
    __name__ = "pip"
    globals = globals()

    @staticmethod
    def generating_distribution_archives():
        """打包软件

        https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives
        """
        from .python import python
        python.m("build")()

    @staticmethod
    def uploading_the_distribution_archives(repository="testpypi"):
        """上传打包文件

        https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives
        https://test.pypi.org/simple/
        """
        from .python import python
        python.m("twine")(f"upload --repository {repository} dist/*")


@Pip.subcommand
class Config(SubCommand):
    __name__ = "config"


@Pip.subcommand
class Show(SubCommand):
    __name__ = "show"


@Pip.subcommand
class List(SubCommand):
    __name__ = "list"


pip = Pip()