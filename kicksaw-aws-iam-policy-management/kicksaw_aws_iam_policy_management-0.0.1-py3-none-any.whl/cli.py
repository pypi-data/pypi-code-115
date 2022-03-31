import click

from kicksaw_aws_iam_policy_management.script import sync_iam

@click.command("main")
def main():
    sync_iam()