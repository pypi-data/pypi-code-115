import click

import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("images", short_help="[CWPP] Retrieves deployed images scan reports")
@click.option('-l', '--limit')
@pass_environment
def cli(ctx, limit):
    result = pc_lib.pc_api.images_list_read(query_params={'limit': limit})
    cli_output(result)
