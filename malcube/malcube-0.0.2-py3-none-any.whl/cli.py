import click

from malcube import logo


@click.group()
def entry_point():
    logo.logo()


@entry_point.command('init', short_help='init data')
def init():
    """Init Data"""


@entry_point.command('filename', short_help='your file to analyze')
def file():
    """File"""
