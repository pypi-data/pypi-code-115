"""Main CLI application"""
import json
from time import time

import click

from kiraak.config import API, Auth
from kiraak.main import main
from kiraak.get_catalog import download_catalog
import kiraak.sync

@click.group()
def cli():
    """Kiraak CLI"""
    pass

@cli.command()
@click.argument(
    "json_file", type=click.Path(exists=True, dir_okay=False)
)
def add(json_file: str) -> None:
    """Add orders using the Kiraak API"""
    try:
        with open(json_file, "r") as file:
            json.load(file)
    except json.JSONDecodeError as err:
        click.echo("File must be a valid JSON file!")
        raise click.Abort() from err

    click.echo(f"Adding orders from {json_file}")
    main(json_file)


@cli.command()
def clear() -> None:
    "Clear login data and credentials"
    Auth.CONF_FILE.unlink()
    API.TOKEN_FILE.unlink()

@cli.command()
def catalog() -> None:
    "Download the current catalog from Kiraak"
    download_catalog()

@cli.command()
@click.option("--once", is_flag=True)
@click.option("--time-gap", default=300, type=int)
def sync(once, time_gap) -> None:
    """Synchronizes the catalog"""
    kiraak.sync.main(once, time_gap)
    