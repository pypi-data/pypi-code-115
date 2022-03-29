#!/usr/bin/env python3

import pytest

from dataclasses import dataclass
from cho_util.app.with_cli import with_cli


@dataclass
class AppConfig:
    num_iter: int = 128


def inner_main(cfg: AppConfig):
    return cfg.num_iter

def invalid_inner_main(cfg):
    return cfg.num_iter

def test_cli():
    assert with_cli(inner_main)() == 128
    assert with_cli(AppConfig)(inner_main)() == 128
    assert with_cli(AppConfig(num_iter=64))(inner_main)() == 64
    assert with_cli(argv=['--num_iter', '32'])(inner_main)() == 32
    assert with_cli(argv=[])(inner_main)() == 128

    with_cli(AppConfig)(invalid_inner_main)()
    with_cli(cls=AppConfig)(invalid_inner_main)()



if __name__ == '__main__':
    test_cli()
