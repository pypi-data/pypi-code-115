import yaml
from runners.pythonrunner import PythonRunner
from exceptions import NonZeroRetcode, ConfigException


class DummyRunner():
    def __init__(self, type) -> None:
        self.type = type

    def run(self, command, workdir=None, env=None):
        raise Exception(f"Invalid runner type in config: {self.type}")


class Job():
    def __init__(self, type, repoDir, vpython, workspace, env={}) -> None:
        self.runner = self.__get_runner(type, repoDir, vpython)
        self.commands = []
        self.workspace = workspace
        self.env = env

    def __get_runner(self, type, repoDir, vpython):
        if type == "python":
            return PythonRunner(repoDir, vpython)
        else:
            return DummyRunner(type)

    def run_commands(self, _env={}):
        try:
            if self.env is None:
                env = _env.copy()
            else:
                env = self.env.copy()
                env.update(_env)
            for command in self.commands:
                self.runner.run(command, self.workspace, env)
        except NonZeroRetcode as n:
            print(n)
            exit(1)


class ConfigParser:
    def __init__(self, file_path, factory) -> None:
        with open(file_path) as f:
            self.config = yaml.safe_load(f)
        self.factory = factory
        if "runners" in self.config:
            if "global" in self.config["runners"]:
                self.factory.set_globals(self.__gen_globals())
            self.factory.update_runners(self.config["runners"])
        self.jobs = self.__get_jobs()

    # Initialize env, workdir if not present
    def __gen_globals(self):
        globals = self.config["runners"]["global"]
        if "env" not in globals:
            globals["env"] = []
        if "workdir" not in globals:
            globals["workdir"] = None
        return globals

    def __get_jobs(self):
        if "jobs" in self.config:
            jobs = {}
            for job_spec in self.config["jobs"]:
                name = job_spec["name"]
                if name in jobs:
                    raise ConfigException(f"Job with name {name} already exists!")

                jobs[name] = job_spec
            return jobs
        else:
            raise ConfigException("No jobs defined in config")

    def execute_job(self, job_name):
        if job_name in self.jobs:
            # Pass the job_spec to a runner
            runner = self.factory.get_runner(self.jobs[job_name]["type"])
            runner.run(self.jobs[job_name])
