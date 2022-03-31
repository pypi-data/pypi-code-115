from __future__ import annotations

import argparse
import hashlib
import io
from typing import Sequence, TextIO
import toml


def find_annonations(files: Sequence[str], annotation: str) -> io.StringIO:

    title = annotation.strip("#:")
    tmp_output = io.StringIO()

    tmp_output.write("## " + title + " List\n")
    tmp_output.write("|File:Line|Date|Comment|\n")
    tmp_output.write("|---|---|---|\n")

    for filename in files:
        try:
            with open(filename, encoding="UTF-8") as f:
                for line_number, line in enumerate(f, 1):
                    if line.startswith(annotation):
                        message = line.split(":")
                        tmp_output.write(
                            "| "
                            + filename
                            + ":"
                            + str(line_number)
                            + " |"
                            + message[1]
                            + "|"
                            + message[2].strip("\n")
                            + "|"
                            + "\n"
                        )
                tmp_output.write("\n\n")
        except Exception as e:
            print(e)

    return tmp_output


def compare_files(output: TextIO, current: io.StringIO) -> bool:
    current_hash = hashlib.sha256(output.read().encode("utf-8")).hexdigest()
    new_hash = hashlib.sha256(current.getvalue().encode("utf-8")).hexdigest()

    if current_hash == new_hash:
        return True
    else:
        return False


def load_config(file_name: str) -> dict:
    try:
        toml_config = toml.load(file_name)
        return toml_config
    except Exception as e:
        print(e)


def filter_files(file_suffix: str, filenames: str) -> Sequence[str]:

    to_process = []

    for suffix in file_suffix:
        for file in filenames:
            if file.endswith(suffix):
                to_process.extend(file)

    return to_process


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser("Create TODO.md from TODO comments in Terraform")
    parser.add_argument("filenames", nargs="*", help="Filenames to check")
    parser.add_argument(
        "--config",
        help="Config file name",
        dest="config_file",
        default=".tf-annotations.toml",
    )
    args = parser.parse_args(argv)

    toml_config = load_config(args.config_file)

    try:
        output_file = open(toml_config["output_file"], "w+")
    except Exception as e:
        print(e)
        return 1

    to_process = []
    to_process = filter_files(toml_config["file_suffix"], args.filenames)
    new_report = io.StringIO()

    for comment in toml_config["comment_syntax"]:
        for header in toml_config["headers"]:
            new_report.write(
                find_annonations(to_process, comment + header + ":").getvalue()
            )

    if not compare_files(output_file, new_report):
        output_file.write(new_report.getvalue())

    output_file.close()

    return 0
