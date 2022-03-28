import click

import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("policy", short_help="[CSPM] Returns available policies, both system default and custom")
@pass_environment
def cli(ctx):
    result = pc_lib.pc_api.policy_list_read()
    cli_output(result)
