import logging

from felia._internal import RootCommand, change_workdir, config

logger = logging.getLogger('Sphinx')
h = logging.StreamHandler()
h.setFormatter(logging.Formatter("%(levelname)s - | %(message)s"))
logger.addHandler(h)
logger.setLevel(logging.INFO)


class SphinxQuickstart(RootCommand):
    """初始化sphinx项目
    """
    __name__ = 'sphinx-quickstart'
    __main__ = 'sphinx.cmd.quickstart.main'
    globals = globals()


class SphinxBuild(RootCommand):
    """
    usage: sphinx-build [OPTIONS] SOURCEDIR OUTPUTDIR [FILENAMES...]
    """
    __name__ = 'sphinx-build'
    __main__ = 'sphinx.cmd.build.main'
    globals = globals()

    def set_params(self):
        self.add_param("-W",
                       help_text="将警告信息转为错误，即遇到警告信息时退出程序")

    def make_html(self):
        self("source",
             "build")


sphinx_quickstart = SphinxQuickstart()
sphinx_build = SphinxBuild()

change_workdir(config["SPHINX"])