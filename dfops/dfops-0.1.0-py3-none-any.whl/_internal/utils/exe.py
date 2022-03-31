from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dfops._internal.types import Tuple


def run_command(
    *cmd: str,
    stdin: int = subprocess.PIPE,
    stdout: int = subprocess.PIPE,
    stderr: int = subprocess.PIPE,
) -> Tuple[int, bytes | None, bytes | None]:
    with subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr) as proc:
        stdout_b, stderr_b = proc.communicate()
    return_code = proc.returncode

    return return_code, stdout_b, stderr_b


def cmd_output(*cmd: str) -> Tuple[int, str | None, str | None]:
    return_code, stdout_b, stderr_b = run_command(*cmd)

    return (
        return_code,
        stdout_b if stdout_b is None else stdout_b.decode(),
        stderr_b if stderr_b is None else stderr_b.decode(),
    )
