import yaml
import shlex
from pythonrunner import PythonRunner
from exceptions import NonZeroRetcode


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


class JobParser:
    def __init__(self, file_path, repoDir, virtual_python) -> None:
        with open(file_path) as f:
            self.config = yaml.safe_load(f)
        self.jobs = self.__get_jobs(repoDir, virtual_python)

    def __get_jobs(self, repoDir, virtual_python):
        if "jobs" in self.config:
            jobs = {}
            for job_spec in self.config["jobs"]:
                name = job_spec["name"]
                if name in jobs:
                    raise Exception(f"Job with name {name} already exists!")

                job = Job(job_spec["type"],
                          repoDir,
                          virtual_python,
                          job_spec.get("workdir", None),
                          job_spec.get("env", None))

                for cmd in job_spec["commands"]:
                    job.commands.append(shlex.split(cmd))
                jobs[name] = job
            return jobs

        else:
            raise Exception("No jobs defined in config")

    def get_modules(self):
        modules = []
        if "runners" in self.config:
            if "python" in self.config["runners"]:
                if "dependencies" in self.config["runners"]["python"]:
                    for dep in self.config["runners"]["python"]["dependencies"]:
                        # (name, i_name) if i_name is defined, else (name, name)
                        modules.append((dep["name"], dep.get("import_name", dep["name"])))
        return modules
