from qplay_cli.api_clients.instance_api import InstanceAPIClient
from qplay_cli.config.qplay_config import QplayConfig
import click
import subprocess

@click.group()
def machine():
    pass

@machine.command()
def launch():
    credentials = QplayConfig.get_credentials()
    access_token = credentials['DEFAULT']['access_token']

    print("Enter lease time in hours")
    lease_time = input()

    response = InstanceAPIClient().launch_machine(access_token, lease_time)
    print(response['message'])

@machine.command()
def ssh():

    bshCmd = 'ssh -i "{}/user-machine.pem" ubuntu@ec2-65-1-134-127.ap-south-1.compute.amazonaws.com'.format(QplayConfig.config_path)
    process = subprocess.Popen(bshCmd.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]