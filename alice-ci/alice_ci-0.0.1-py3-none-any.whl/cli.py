# Sourcefor App class:
# https://stackoverflow.com/questions/57593111/how-to-call-pip-from-a-python-script-and-make-it-install-locally-to-that-script
import os
import sys
import subprocess
import argparse


class App:
    def __init__(self, virtual_dir):
        self.virtual_dir = virtual_dir
        if os.name == "nt":
            self.virtual_python = os.path.join(self.virtual_dir, "Scripts", "python.exe")
        else:
            self.virtual_python = os.path.join(self.virtual_dir, "bin", "python3")

    def install_virtual_env(self):
        self.pip_install("virtualenv")
        if not os.path.exists(self.virtual_python):
            import subprocess
            subprocess.call([sys.executable, "-m", "virtualenv", self.virtual_dir])
        else:
            print("found virtual python: " + self.virtual_python)

    def is_venv(self):
        return sys.prefix == self.virtual_dir

    def restart_under_venv(self):
        print("Restarting under virtual environment " + self.virtual_dir)
        with subprocess.Popen([self.virtual_python, __file__] + sys.argv[1:]) as p:
            p.wait()
            exit(p.returncode)

    def pip_install(self, package, import_name=None):
        try:
            if import_name is None:
                __import__(package)
            else:
                __import__(import_name)
        except:  # noqa: E722
            subprocess.call([sys.executable, "-m", "pip", "install", package, "--upgrade"])

    def __gen_env(self, param_list):
        env_vars = {}
        for item in param_list:
            item_parts = item.split("=")
            if len(item_parts) == 2:
                env_vars[item_parts[0]] = item_parts[1]
        return env_vars

    def run(self, args, repoDir):
        if not self.is_venv():
            self.install_virtual_env()
            self.restart_under_venv()
        else:
            print("Running under virtual environment")
            # TODO: yaml is only used in venv, yet installed as dependency in setup.cfg
            self.pip_install("pyyaml", "yaml")

            from jobparser import JobParser
            jobParser = JobParser(args.input, repoDir, self.virtual_python)
            for name, import_name in jobParser.get_modules():
                self.pip_install(name, import_name)

            print("Begin pipeline steps...")
            for step in args.steps:
                if step in jobParser.jobs:
                    jobParser.jobs[step].run_commands(self.__gen_env(args.env))
                    print(f"Step {step}: SUCCESS")
                else:
                    print(f"Step {step} not found in {args.input}")
                    exit(1)


def main():
    pathToScriptDir = os.path.dirname(os.path.realpath(__file__))
    repoDir = os.path.join(pathToScriptDir, "..")
    app = App(os.path.join(pathToScriptDir, "venv"))

    parser = argparse.ArgumentParser()
    parser.add_argument("steps", nargs='+')
    parser.add_argument("-i", "--input", default="alice-ci.yaml")
    parser.add_argument("-e", "--env", nargs='*', default=[])
    args = parser.parse_args()
    if not os.path.isfile(args.input):
        print(f"No such file: {args.input}")
        exit(1)
    app.run(args, repoDir)


if __name__ == "__main__":
    main()
