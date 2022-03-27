# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Parse command-line arguments. """

import argparse
import logging

import mrtest.add_packages
import mrtest.origin
import mrtest.zap_packages

try:
    import argcomplete
except ImportError:
    argcomplete = False


def parse_args_parser_add(sub):
    """ :param sub: argparser's subparser """
    parser = sub.add_parser("add", help="install/upgrade to packages from a MR")
    parser.add_argument("-a", "--alpine", action="store_true",
                        help="use alpine's aports instead of pmOS' pmaports")
    parser.add_argument("mr_id", type=int, help="merge request ID")


def parse_args_parser_zap(sub):
    """ :param sub: argparser's subparser """
    sub.add_parser("zap", help="uninstall previously added packages")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--no-cache", action="store_true",
                        help="do not use local cache for MR information")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="display debug log: all commands and locations of"
                             " http cache files")
    sub = parser.add_subparsers(title="action", dest="action")
    sub.required = True

    parse_args_parser_add(sub)
    parse_args_parser_zap(sub)

    if argcomplete:
        argcomplete.autocomplete(parser, always_complete_options="long")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.action == "add":
        origin = mrtest.origin.aports if args.alpine else mrtest.origin.pmaports
        mrtest.add_packages.add_packages(origin, args.mr_id, args.no_cache)
    elif args.action == "zap":
        mrtest.zap_packages.zap_packages()
