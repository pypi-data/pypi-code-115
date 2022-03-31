import os
import subprocess
import yaml

from alice.exceptions import ConfigException


class ConfigParser:
    def __init__(self, file_path, factory, verbose=False) -> None:
        self.verbose = verbose
        with open(file_path) as f:
            self.config = yaml.safe_load(f)
        self.factory = factory
        self.factory.set_globals(self.__gen_globals())
        if "runners" in self.config:
            self.factory.update_runners(self.config["runners"])
        self.jobs = self.__get_jobs()

    # Initialize env, workdir if not present
    def __gen_globals(self):
        globals = {
            "env": [],
            "workdir": None
        }
        if "runners" in self.config:
            if "global" in self.config["runners"]:
                if "env" in self.config["runners"]["global"]:
                    globals["env"] = self.config["runners"]["global"]["env"]
                if "workdir" in self.config["runners"]["global"]:
                    globals["workdir"] = self.config["runners"]["global"]["workdir"]
        
        if (self.verbose):
            print(f"[Alice] Configured globals: {globals}")
        return globals

    def __get_jobs(self):
        if "jobs" in self.config:
            jobs = {}
            for job_spec in self.config["jobs"]:
                name = job_spec["name"]
                if name in jobs:
                    raise ConfigException(f"Job with name {name} already exists!")

                jobs[name] = job_spec
            if (self.verbose):
                print(f"[Alice] Parsed jobs: {', '.join(jobs.keys())}")
            return jobs
        else:
            raise ConfigException("No jobs defined in config")

    def __is_changed(self, changes):
        try:                
            target = changes["branch"]
            paths = []
            for path in changes["paths"]:
                paths.append(os.path.abspath(path))
            print(paths)
            # TODO: Error handling
            command = ["git", "diff", "--name-only", target]
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
                p.wait()
                for line in p.stdout:
                    change_path = os.path.abspath(line.decode("UTF-8").strip())
                    for path in paths:
                        spec_path = os.path.abspath(path)
                        if change_path.startswith(spec_path):
                            print(f"Modified file: {change_path}")
                            print(f"Path match: {path}")
                            return True
        except KeyError:
            raise ConfigException(f"Invalid 'changes' config: {changes}")
        return False

    def execute_job(self, job_name):
        if job_name in self.jobs:
            job_spec = self.jobs[job_name]
            should_run = True
            if "changes" in job_spec:
                should_run = self.__is_changed(job_spec["changes"])
            if should_run:
                runner = self.factory.get_runner(job_spec["type"])
                runner.run(job_spec)
                return "SUCCESS"
            else:
                print("SKIP, no change detected")

