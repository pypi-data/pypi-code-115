#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import click
import easy_scraper


def writer(item: dict, format: str) -> str:
    if format == "ltsv":
        return "\t".join(f"{k}:{v}" if k else v for (k, v) in item.items())

    elif format == "json":
        return json.dumps(item)

    else:
        raise NotImplementedError


@click.command()
@click.option("--delimiter", "-d", default="\t")
@click.option("--format", "-f", default="ltsv", type=click.Choice(["ltsv", "json"]))
@click.argument("pattern")
def main(delimiter: str, format: str, pattern: str):
    """web-grep

    Read Xml or Html from stdin,
    Write into stdout.
    """
    html = "\n".join(sys.stdin)
    res = easy_scraper.match(html, pattern)
    for item in res:
        print(writer(item, format))


if __name__ == "__main__":
    main()
