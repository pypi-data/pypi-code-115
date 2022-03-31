# SPDX-FileCopyrightText: © Antonio López Rivera <antonlopezr99@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""
CLI
---
"""


import argparse

from emblem import coverage


def main():

    CLI = argparse.ArgumentParser()

    # Declare arguments
    CLI.add_argument(
        'coverage',
        help='code coverage percentage'
    )
    CLI.add_argument(
        '--colors',
        nargs='*',
        type=str,
        default=['#b00909', '#3ade65'],
        required=False,
        help='colors from which to generate a linear\
              segmented colormap, low to high'
    )
    CLI.add_argument(
        '--cmap',
        nargs=1,
        type=str,
        default=False,
        required=False,
        help='matplotlib colormap'
    )

    # Parse arguments
    args = CLI.parse_args()

    print(coverage(args.coverage, colors=args.colors, cmap=args.cmap[0] if args.cmap else None))


if __name__ == '__main__':
    main()