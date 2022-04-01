#!/usr/bin/env python3
#
# Simple utility to generate paragraphs of text.
# ================================================================

import sys

from ee059f4560b24ba78d7c30103ea49713 import gen_paragraphs


# ----------------------------------------------------------------
# Constants

program = 'generate'
version = '0.0.1'


# ----------------------------------------------------------------

def main():
    exe = sys.argv.pop(0)

    num_para = 1
    do_version = False
    do_help = False

    while 0 < len(sys.argv):
        option = sys.argv.pop(0)

        if option == '-h' or option == '--help':
            do_help = True

        elif option == '--version':
            do_version = True

        else:
            try:
                num_para = int(option)
            except ValueError:
                if option.startswith('-'):
                    print(f'Usage error: unknown option: {option}')
                else:
                    print(f'Usage error: number of paragraphs not an integer: {option}')
                exit(2)

    if do_help:
        print('Usage: generate [options] [num_paragraphs]')
        print('Options')
        print('       --version  display version information and exit')
        print('  -h | --help     display this help and exit')
        exit(0)

    if do_version:
        print(f'{program} {version}')
        exit(0)

    first = True
    for p in gen_paragraphs(num_para):
        if first:
            first = False
        else:
            print()
        print(p)


# ----------------------------------------------------------------
# Main entry point

if __name__ == '__main__':
    main()

# EOF
