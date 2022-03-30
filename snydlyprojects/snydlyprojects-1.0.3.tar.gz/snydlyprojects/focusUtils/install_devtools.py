from fabric import Connection
from invoke import Responder
import os
import sys
from constants import SUDOPASS, SSHPASS

def install_devtools(ip_address):
    print('Made it to function')
    hudl_tegra_key_path = os.path.expanduser(os.path.join("~", ".ssh", "hudl_tegra_key"))
    host = f'ubuntu@{ip_address}'

    connection = Connection(host = host, connect_kwargs = {"key_filename": hudl_tegra_key_path, "password": SSHPASS})
    sudopass = Responder(
        pattern=r'\[sudo\] password for ubuntu:',
        response=f'{SUDOPASS}\n'
    )
    connection.run("sudo apt-get update", pty=True, watchers=[sudopass])
    connection.run("sudo apt-get install focus-devtools/stable", pty=True, watchers=[sudopass])