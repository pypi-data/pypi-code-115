#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass

import click
import easy_scraper


@dataclass
class Pattern:
    format: str

    @classmethod
    def build(cls, raw_format: str) -> Pattern:
        """Build pattern for easy_scraper

        Examples
        --------
        >>> build("<img src={} />")
        Pattern("<img src={{}} />")
        >>> build("<a href={x}>{y}</a>")
        Pattern("<a href={{x}}>{{y}}</a>")
        """
        format = raw_format

        annoyholder = re.compile(r"{\s*}")
        format = annoyholder.sub(r"{{}}", format)

        namedholder = re.compile(r"{\s*(\w+)\s*}")
        format = namedholder.sub(r"{{\1}}", format)

        return Pattern(format)


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
    p = Pattern.build(pattern)
    res = easy_scraper.match(html, p.format)
    for item in res:
        print(writer(item, format))


if __name__ == "__main__":
    main()
