import datetime
import logging
import os
import subprocess
from dataclasses import dataclass

from .configs import ExecutionStatus, ReturnCodeStatus
from .errors import ExecutionException

logger = logging.getLogger("bundletool")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class PyBundletool(type):
    def __init__(
        cls,
        name,
        bases,
        dct,
    ):
        """
        Supported  systems and platforms:

            # system            #platforms

            Linux                   x86_64
            Darwin                arm64
            Darwin                x86_64
        """

        super().__init__(name, bases, dct)
        cls.return_code = None

        cls._bundletool_file_path = os.path.join(
            os.path.join(BASE_DIR, "binary-files", "bundletool")
        )
        cls._aapt2 = os.path.join(os.path.join(BASE_DIR, "binary-files", "aapt2"))

    def _execute(cls, command):
        logger.info(
            {
                "status": ExecutionStatus.STARTING,
                "time": datetime.datetime.now(),
                "command": command,
            }
        )

        task = subprocess.run(
            command,
            text=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        cls.return_code = task.returncode

        execution_log = {
            "status": ExecutionStatus.SUCCESSFUL
            if cls.return_code == ReturnCodeStatus.SUCCESSFUL
            else ExecutionStatus.FAILED,
            "stderr": task.stderr,
            "stdout": task.stdout,
            "return_code": cls.return_code,
        }

        if cls.return_code == ReturnCodeStatus.FAILED:
            raise ExecutionException(execution_log)

        logger.info({**execution_log, "time": datetime.datetime.now()})

        return execution_log


@dataclass
class BuildApks(metaclass=PyBundletool):
    bundle: str
    output: str
    ks: str = ""
    ks_pass: str = ""
    ks_key_alias: str = ""
    key_pass: str = ""
    overwrite: bool = False
    aapt2: str = ""
    connected_device: bool = False
    device_id: str = ""
    device_spec: str = ""
    mode_universal: bool = True
    local_testing: bool = False
    bundletool: str = ""

    def __post_init__(self):
        if not self.bundletool:
            self.bundletool = self._bundletool_file_path
        if not self.aapt2:
            self.aapt2 = self._aapt2

        self.command = [self.bundletool, "build-apks"] + self.build_command(
            flags=self.__dict__
        )

    def execute(self):
        return self.__class__._execute(command=self.command)

    def build_command(self, flags: dict):
        command = []

        config = {
            "bundle": f'--bundle={flags.get("bundle")}',
            "output": f'--output={flags.get("output")}',
            "ks": f'--ks={flags.get("ks")}',
            "ks_pass": f'--ks-pass={flags.get("ks_pass")}',
            "ks_key_alias": f'--ks-key-alias={flags.get("ks_key_alias")}',
            "key_pass": f'--key-pass={flags.get("key_pass")}',
            "overwrite": "--overwrite",
            "aapt2": f'--aapt2={flags.get("aapt2")}',
            "connected_device": "--connected-device",
            "device_id": f'--device-id={flags.get("device_id")}',
            "device_spec": f'--device-spec={flags.get("device_spec")}',
            "mode_universal": "--mode=universal",
            "local_testing": "--local-testing",
        }

        for key in flags:
            if key in config.keys() and flags.get(key):
                command.append(config.get(key))

        return command


@dataclass
class Version(metaclass=PyBundletool):
    bundletool: str = ""

    def __post_init__(self):
        if not self.bundletool:
            self.bundletool = self._bundletool_file_path

        self.command = [self.bundletool, "version"]

    def execute(self):
        output = self.__class__._execute(command=self.command)
        return output
