from os import getcwd

from alice.runners.pythonrunner import PythonRunner
from alice.exceptions import ConfigException


class Factory():
    def __init__(self, verbose) -> None:
        self.verbose = verbose
        self.runnertypes = self.__load_runners()
        self.runners = {}
        self.workdir = getcwd()
        self.globals = {}

    def __load_runners(self):
        # TODO: Runners can be imported via cli too
        # module = __import__("module_file")
        # my_class = getattr(module, "class_name")
        runners = {"python": PythonRunner}

        if (self.verbose):
            print(f"[Alice] Available runners: {'|'.join(runners.keys())}")
        return runners

    def set_globals(self, globals):
        self.globals = globals

    def update_globals(self, update):
        if "env" in update:
            self.globals["env"].update(update["env"])

    def update_runners(self, config):
        for runnertype, runnerconfig in config.items():
            if runnertype != "global":
                if (self.verbose):
                    print(f"[Alice] Configuring runner {runnertype}")
                self.get_runner(runnertype).update_config(runnerconfig)

    def get_runner(self, runnertype):
        if runnertype not in self.runners:
            if runnertype in self.runnertypes:
                if (self.verbose):
                    print(f"[Alice] Initializing runner: {runnertype}")
                self.runners[runnertype] = self.runnertypes[runnertype](self.workdir,
                                                                        self.globals,
                                                                        self.verbose)
            else:
                raise ConfigException(f"Invalid runner type: {runnertype}")
        return self.runners[runnertype]
