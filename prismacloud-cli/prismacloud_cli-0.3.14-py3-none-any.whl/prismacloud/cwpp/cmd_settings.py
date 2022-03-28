import click
import prismacloud.api as pc_lib
from prismacloud.cli import cli_output, pass_environment


@click.command("settings", short_help="[CWPP] Shows CWPP settings.")
@pass_environment
def cli(ctx):
    result = pc_lib.get_endpoint("settings/defender")
    cli_output(result)
