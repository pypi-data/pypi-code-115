import click

import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("repositories", short_help="[PCCS] Output details about the repositories onboardes to PCCS")
@pass_environment
def cli(ctx):
    result = pc_lib.pc_api.repositories_list_read(query_params = {'errorsCount': 'true'})
    cli_output(result)
