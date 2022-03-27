"""
CLI for the SMAT API.
"""

import datetime
import json

import click

from smat_cli import Smat, SmatError


def until_default():
    return (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")


@click.group()
def main():
    """
    smat is a tool for querying the Social Media Analysis Toolkit (https://www.smat-app.com). It supports querying
    via the public API, which may be subject to rate limits, and responses may take substantial time if the server is
    busy. All commands can accept ElasticSearch simple search string syntax (see ElasticSearch documentation).

    \f
    This is the main Click group for the cli, accessible via the package's entrypoint "smat".
    """
    pass


@main.command()
@click.option(
    "--limit",
    "-l",
    default=10,
    type=int,
    help="Maximum number of results to return.",
    show_default=True,
)
@click.option(
    "--site",
    "-s",
    required=True,
    help="The site to get the content from.",
)
@click.option(
    "--since",
    default=until_default(),
    type=click.DateTime(),
    help="Earliest datetime of the content to return.",
    show_default=True,
)
@click.option(
    "--until",
    type=click.DateTime(),
    help="Latest datetime of the content to return.",
)
@click.argument("query", type=str)
def content(limit, site, since, until, query):
    """
    Get content matching a query from a site.

    \f
    A Click command for the main group that makes requests to the /content endpoint and outputs JSON results.
    """
    api = Smat()
    try:
        for result in api.content(
            term=query, limit=limit, site=site, since=since, until=until
        ):
            click.echo(json.dumps(result))
    except SmatError as e:
        click.echo("Error: " + str(e))


@main.command()
@click.option(
    "--site",
    "-s",
    required=True,
    help="The site to get the content from.",
)
@click.option(
    "--since",
    default=until_default(),
    type=click.DateTime(),
    help="Earliest datetime of the content to return.",
    show_default=True,
)
@click.option(
    "--until",
    type=click.DateTime(),
    help="Latest datetime of the content to return.",
)
@click.option(
    "--interval",
    "-i",
    type=str,
    help="Interval for the data being returned.",
)
# @click.option(
#     "--changepoint/--no-changepoint",
#     type=bool,
#     default=False,
#     help="Changepoint help goes here.",
# )
@click.argument("query", type=str)
def timeseries(query, interval, site, since, until, changepoint=False):
    """
    Get timeseries matching a query from a site.

    \f
    A Click command for the main group that makes requests to the /timeseries endpoint and outputs JSON results.
    """
    api = Smat()
    try:
        for result in api.timeseries(
            term=query,
            since=since,
            until=until,
            interval=interval,
            site=site,
            changepoint=changepoint,
        ):
            click.echo(json.dumps(result))
    except SmatError as e:
        click.echo("Error: " + str(e))


@main.command()
@click.option(
    "--site",
    "-s",
    required=True,
    help="The site to get the content from.",
)
@click.option(
    "--since",
    default=until_default(),
    type=click.DateTime(),
    help="Earliest datetime of the content to return.",
    show_default=True,
)
@click.option(
    "--until",
    type=click.DateTime(),
    help="Latest datetime of the content to return.",
)
@click.option(
    "--agg-by",
    "-a",
    type=str,
    required=True,
    help="Response key to aggregate by.",
)
@click.argument("query", type=str)
def activity(query, site, since, until, agg_by):
    """
    Get activity aggregated by key matching a query from a site.

    The agg-by option for this command is the key to use for the aggregation and the possible options can vary depending
    on which site is being queried. For example, `--agg-by channelusername --site telegram trump` will aggregate all
    mentions of Trump on Telegram by channel. In order to better understand the available keys for aggregation, using
    the `content` tool can provide some examples.

    \f
    A Click command for the main group that makes requests to the /activity endpoint and outputs JSON results.
    """
    api = Smat()
    try:
        for result in api.activity(
            term=query,
            since=since,
            until=until,
            site=site,
            agg_by=agg_by,
        ):
            click.echo(json.dumps(result))
    except SmatError as e:
        click.echo("Error: " + str(e))


@main.command()
def sites():
    """
    Show a list of available sites.

    \f
    A Click command for the main group that outputs a list of sites available via the SMAT API.
    """
    api = Smat()
    for site in sorted(api.sites):
        click.echo(site)


if __name__ == "__main__":
    main()
