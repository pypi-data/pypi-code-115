import subprocess
import os

from exceptions import NonZeroRetcode


class PythonRunner():
    def __init__(self, repo, vpython) -> None:
        self.vpython = vpython
        self.repopath = repo

    def __get_env(self, overrides):
        env = os.environ.copy()
        if overrides is not None:
            for key, value in overrides.items():
                env[key] = value
        return env

    def ghetto_glob(self, command):
        new_command = []
        for item in command:
            if "*" in item:
                dir = os.path.abspath(os.path.dirname(item))
                base_name = os.path.basename(item)
                if os.path.isdir(dir):
                    item_parts = base_name.split("*")
                    print(item_parts)
                    for file in os.listdir(dir):
                        if item_parts[0] in file and item_parts[1] in file:
                            new_command.append(os.path.join(dir, file))
            else:
                new_command.append(item)
        return new_command

    def run(self, command, workdir=None, env=None):
        if workdir is not None:
            pwd = os.path.abspath(os.path.join(self.repopath, workdir))
        else:
            pwd = self.repopath
        run_env = self.__get_env(env)
        run_command = self.ghetto_glob(command)
        if os.path.isdir(pwd):
            with subprocess.Popen([self.vpython] + run_command, cwd=pwd, env=run_env) as p:
                p.wait()
                if p.returncode != 0:
                    raise NonZeroRetcode(f"Command {command} returned code {p.returncode}")
        else:
            raise Exception(f"Invalid path for shell command: {pwd}")
