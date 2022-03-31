import sys as _sys

from dfops._internal.cli.io import ArgumentParser


def main(*argv: str) -> int:
    if not argv:
        argv = tuple(_sys.argv)

    try:
        script_name = argv[0]
    except IndexError:
        script_name = None

    argv = argv[1:]

    parser = ArgumentParser(script_name)
    return parser.run(*argv)
