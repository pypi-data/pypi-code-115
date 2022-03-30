import click

import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("license", short_help="[CWPP] Returns the license stats including the credit per defender")
@pass_environment
def cli(ctx):
    result = pc_lib.get_endpoint("stats/license")
    cli_output(result)
