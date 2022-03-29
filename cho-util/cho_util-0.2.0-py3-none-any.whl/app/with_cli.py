#!/usr/bin/env python3
#PYTHON_ARGCOMPLETE_OK
"""Automatically create argparse parser for CLI arguments from Serializable
dataclass."""

__all__ = ['with_cli']

import sys
from dataclasses import dataclass, is_dataclass
from simple_parsing import ArgumentParser, Serializable
from typing import Callable, List, Type, TypeVar, Union, Optional
import logging
import argparse
import inspect
from pathlib import Path
from functools import wraps

use_argcomplete = False
try:
    import argcomplete
    use_argcomplete = True
except ImportError:
    logging.info('argcomplete disabled due to missing package.')


D = TypeVar("D")


def _update_settings_from_file(opts: dataclass, argv: List[str]):
    """Update given settings from a configuration file."""
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument(
        '--load_config',
        help='Load from configuration file',
        dest='load_config',
        metavar='CONFIG_FILE',
        default='')
    parsed_args, next_argv = config_parser.parse_known_args(argv)

    # If no `config_file` arg, fallback to passthrough behavior.
    if not parsed_args.load_config:
        return (opts, argv, [config_parser])

    config_file = Path(parsed_args.load_config)
    if not config_file.exists():
        logging.error(F'config file = {config_file} does not exist!')
        return (opts, argv, [config_parser])

    opts = opts.load(str(config_file))
    return (opts, next_argv, [config_parser])


def update_settings(opts: dataclass,
                    argv: Optional[List[str]] = None,
                    description: Optional[str] = None):
    """Update given settings from command line arguments.

    Uses `argparse`, `argcomplete` and `simple_parsing` under the hood.
    """
    if not is_dataclass(opts):
        raise ValueError(F'Cannot update args on non-dataclass class : {opts}')
    cls = opts if isinstance(opts, type) else type(opts)

    # Use default system argv if not supplied.
    argv = sys.argv[1:] if argv is None else argv

    # Update from config file, if applicable.
    parser_parents = []
    if issubclass(cls, Serializable):
       opts, argv, parser_parents = _update_settings_from_file(opts, argv)

    # Update from cli args...
    parser = ArgumentParser(parents=parser_parents, description=description)
    if isinstance(opts, type):
        parser.add_arguments(cls, dest='opts')
    else:
        parser.add_arguments(cls, dest='opts', default=opts)
    if use_argcomplete:
        # NOTE(ycho): required to call `_preprocessing()` prior to autocomplete
        # due to some arguments being unfilled up to that point in time.
        parser._preprocessing()
        argcomplete.autocomplete(parser)
    args, unargs = parser.parse_known_args(argv, attempt_to_reorder=True)
    if len(unargs) > 0:
        logging.warn(F'Ignored args = {unargs}')
    return args.opts


def with_cli(cls: Union[Type[D], D] = None, argv: List[str] = None):
    """Decorator for automatically adding parsed args from cli to entry
    point."""

    main = None
    if cls is None:
        # @with_cli()
        need_cls = True
    else:
        if callable(cls) and not is_dataclass(cls):
            # @with_cli
            main = cls
            need_cls = True
        else:
            # @with_cli(cls=Config, ...)
            need_cls = (cls is None)  # FIXME(ycho): always False.

    def decorator(main: Callable[[D], None]):
        # NOTE(ycho):
        # if `cls` is None, try to infer them from `main` signature.
        inner_cls = cls
        if need_cls:
            sig = inspect.signature(main)
            if len(sig.parameters) == 1:
                key = next(iter(sig.parameters))
                inner_cls = sig.parameters[key].annotation
            else:
                raise ValueError(
                    '#arg != 1 in main {}: Cannot infer param type.'
                    .format(sig))

        # If supplied, load from file.
        # The arguments provided through the file will be
        # overridden by any CLI args if present.
        instance = None

        # NOTE(ycho): using @wraps to forward main() documentation.
        @wraps(main)
        def wrapper():
            doc = getattr(main, '__doc__', '')
            opts: D = update_settings(
                inner_cls, argv, description=doc)
            return main(opts)
        return wrapper

    if main is not None:
        return decorator(main)
    else:
        return decorator


def main():
    logging.basicConfig(level=logging.INFO)

    @dataclass
    class Settings:
        value: int = 0

    opts = Settings()
    opts = update_settings(opts)
    logging.info(F'got value = {opts.value}')


@dataclass
class AppConfig(Serializable):
    value: int = 1


@with_cli
def main2(cfg: AppConfig):
    """ @decorator """
    print(cfg)


@with_cli(AppConfig)
def main3(cfg: AppConfig):
    """ @decorator(...) """
    print(cfg)


@with_cli()
def main4(cfg: AppConfig):
    """ @decorator() """
    print(cfg)


@with_cli(AppConfig)
def main5(cfg):
    """ @decorator(cls), without function level type annotation """
    print(cfg)


@with_cli(AppConfig(value=16))
def main6(cfg):
    """ @decorator(cls(*args,**kwds)), i.e. called with instance"""
    print(cfg)


def main7():
    """test all the things."""
    def _main(cfg: AppConfig):
        """type-annotated main()"""
        print(cfg)

    def _main2(cfg):
        """not type-annotated main()"""
        print(cfg)

    # Null case
    _main(AppConfig())
    # case A
    with_cli()(_main)()
    # case B
    with_cli(_main)()
    # case C
    with_cli(AppConfig)(_main)()
    # case C
    with_cli(AppConfig(value=32))(_main)()
    # case C
    with_cli(argv=[])(_main)()
    # case C
    with_cli(argv=['--value', '64'])(_main)()

    # Tests for cases where arg is not type-anntoated:
    # INVALID: case A (cannot infer type)
    # with_cli()(_main2)()
    # INVALID: case B (cannot infer type)
    # with_cli(_main2)()
    # case C
    with_cli(AppConfig)(_main2)()
    with_cli(cls=AppConfig)(_main2)()


if __name__ == '__main__':
    main()
    print(main.__doc__)
    main2()
    print(main2.__doc__)
    main3()
    print(main3.__doc__)
    main4()
    print(main4.__doc__)
    main5()
    print(main5.__doc__)
    main6()
    print(main6.__doc__)
    main7()
    print(main7.__doc__)
