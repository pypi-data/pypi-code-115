import click

import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("version", short_help="[CWPP] Shows CWPP version.")
@pass_environment
def cli(ctx):
    version = pc_lib.get_endpoint("version")
    cli_output(version)
