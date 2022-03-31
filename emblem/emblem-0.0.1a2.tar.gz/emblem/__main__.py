# SPDX-FileCopyrightText: © Antonio López Rivera <antonlopezr99@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""
CLI
---
"""


import argparse

from emblem import coverage


def add(cli, name, help='', nargs=1):
    cli.add_argument(
        f'--{name}',
        nargs=nargs,
        default=None,
        help=help
    )


def main():

    CLI = argparse.ArgumentParser()

    CLI.add_argument(
        'coverage',
        help='code coverage percentage'
    )

    # Declare arguments
    args = {'label':    ['badge label'],
            'style':    ['badge style'],
            'logo':     ['badge logo'],
            'colors':   ['colors from which to generate a linear segmented colormap, low to high', '*'],
            'cmap':     ['matplotlib colormap']}
    for arg in args.keys():
        add(CLI, arg, *args[arg])

    # Parse input
    _input = CLI.parse_args()
    
    # Create input dictionary
    kwargs = {}

    for arg in args.keys():
        if getattr(_input, arg) is not None:
            v = getattr(_input, arg)
            if isinstance(v, list) and len(v) == 1:
                v = v[0]
            kwargs[arg] = v

    print(coverage(_input.coverage, **kwargs))


if __name__ == '__main__':
    main()