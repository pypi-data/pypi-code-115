import click

import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("tags", short_help="[CWPP] Retrieves a list of tags")
@pass_environment
def cli(ctx):
    result = pc_lib.get_endpoint("tags")
    cli_output(result)
