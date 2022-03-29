import subprocess
import os
import sys
import shlex

from alice.exceptions import NonZeroRetcode, RunnerError, ConfigException


# same venv across all runs!
class PythonRunner():
    def __init__(self, workdir, defaults) -> None:
        self.workdir = workdir
        self.virtual_dir = os.path.abspath(os.path.join(workdir, "venv"))
        self.config = defaults
        self.env_vars = os.environ.copy()
        for env_var in defaults["env"]:
            self.env_vars[env_var["name"]] = env_var["value"]

        self.__init_venv()

    def __init_venv(self):
        if os.name == "nt":  # Windows
            self.vpython = os.path.join(self.virtual_dir, "Scripts", "python.exe")
        else:  # Linux & Mac
            self.vpython = os.path.join(self.virtual_dir, "bin", "python3")

        if not os.path.exists(self.vpython):
            with subprocess.Popen([sys.executable, "-m", "virtualenv", self.virtual_dir],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
                p.wait()
                if p.returncode != 0:
                    sys.stdout.buffer.write(p.stderr.read())
                    raise RunnerError("PythonRunner: Could not create virtualenv")
                else:
                    print(f"PythonRunner: Virtualenv initialized at {self.virtual_dir}")
        else:
            print(f"PythonRunner: Found virtualenv at {self.virtual_dir}")

    # Stores common defaults for all jobs - all types!
    # Also - dependency install by config is only allowed in this step
    def update_config(self, config):
        if "dependencies" in config:
            for dependency in config["dependencies"]:
                # TODO: Check what happens with fixed version
                command = [self.vpython, "-m", "pip", "install", dependency, "--upgrade"]
                with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
                    p.wait()
                    if p.returncode != 0:
                        sys.stdout.buffer.write(p.stderr.read())
                        raise(RunnerError(f"PythonRunner: Could not install dependency: {dependency} ({p.returncode})"))
        if "env" in config:
            for env_var in config["env"]:
                self.env_vars[env_var["name"]] = env_var["value"]
        if "workdir" in config and config["workdir"] is not None:
            self.workdir = os.path.join(self.workdir, config["workdir"])

    def __ghetto_glob(self, command):
        new_command = []
        for item in command:
            if "*" in item:
                dir = os.path.abspath(os.path.dirname(item))
                base_name = os.path.basename(item)
                if os.path.isdir(dir):
                    item_parts = base_name.split("*")
                    for file in os.listdir(dir):
                        # TODO: Fix ordering! A*B = B*A = AB*
                        if item_parts[0] in file and item_parts[1] in file:
                            new_command.append(os.path.join(dir, file))
            else:
                new_command.append(item)
        return new_command

    # Executes the given job in the one and only venv
    # parameter shall be the raw jobscpec
    def run(self, job_spec):
        if "workdir" in job_spec:
            pwd = os.path.abspath(os.path.join(self.workdir, job_spec["workdir"]))
        else:
            pwd = self.workdir
        run_env = self.env_vars.copy()
        if "env" in job_spec:
            for env_var in job_spec["env"]:
                run_env[env_var["name"]] = env_var["value"]
        if "commands" in job_spec:
            commands = job_spec["commands"]
            for command in commands:
                # TODO: only split if command is not an array
                run_command = self.__ghetto_glob(shlex.split(command))
                if os.path.isdir(pwd):
                    with subprocess.Popen([self.vpython] + run_command, cwd=pwd, env=run_env) as p:
                        p.wait()
                        if p.returncode != 0:
                            raise NonZeroRetcode(f"Command {command} returned code {p.returncode}")
                else:
                    raise RunnerError(f"PythonRunner: Invalid path for shell command: {pwd}")
        else:
            raise ConfigException(f"PythonRunner: No commands specified in step {job_spec['name']}")
