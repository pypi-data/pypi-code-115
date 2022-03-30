import click

import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("intelligence", short_help="[CWPP] Output details about the intelligence stream")
@pass_environment
def cli(ctx):
    result = pc_lib.pc_api.statuses_intelligence()
    cli_output(result)
