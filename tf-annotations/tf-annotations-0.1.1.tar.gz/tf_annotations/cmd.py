from __future__ import annotations

import argparse
import glob
from typing import Sequence, TextIO
from datetime import datetime
import toml


def write_footer(file: TextIO):
    file.write(
      "`Date Generate: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + "`\n\n"
    )


def find_annonations(files: Sequence[str], output: TextIO, annotation: str):

    title = annotation.strip("#:")

    output.write("## " + title + " List\n")
    output.write("|File:Line|Date|Comment|\n")
    output.write("|---|---|---|\n")

    for filename in files:
        try:
            with open(filename, encoding="UTF-8") as f:
                for line_number, line in enumerate(f, 1):
                    if line.startswith(annotation):
                        message = line.split(":")
                        output.write(
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
                output.write("\n\n")
        except Exception as e:
            print(e)


def load_config(file_name: str) -> dict:
    try:
        toml_config = toml.load(file_name)
        return toml_config
    except Exception as e:
        print(e)


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser("Create TODO.md from TODO comments in Terraform")
    parser.add_argument(
        "--config",
        help="Config file name",
        dest="config_file",
        default=".tf-annotations.toml",
    )
    args = parser.parse_args(argv)

    toml_config = load_config(args.config_file)

    try:
        output_file = open(toml_config["output_file"], "w")
    except Exception as e:
        print(e)

    to_process = []
    comment_syntax = toml_config["comment_syntax"]
    for files in toml_config["file_suffix"]:
        to_process.extend(glob.glob(files))

    for comment in comment_syntax:
        for header in toml_config["headers"]:
            find_annonations(to_process, output_file, comment + header + ":")

    write_footer(output_file)
    output_file.close()

    retval = 0

    return retval
