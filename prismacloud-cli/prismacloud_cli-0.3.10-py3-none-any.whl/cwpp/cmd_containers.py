import click
import prismacloud.api as pc_lib
from prismacloud.cli import pass_environment, cli_output

@click.group("containers", short_help="[CWPP] Container scan reports.")
@pass_environment
def cli(ctx):
    pass

@click.command()
def list():
    result = pc_lib.get_endpoint("containers")
    cli_output(result)

@click.command()
def names():
    result = pc_lib.get_endpoint("containers/names")
    cli_output(result)

@click.command()
def count():
    result = pc_lib.get_endpoint("containers/count")
    cli_output(result)

cli.add_command(list)
cli.add_command(names)
cli.add_command(count)