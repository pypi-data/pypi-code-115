from fabric import Connection
from invoke import Responder
import os
import sys
from constants import SUDOPASS, SSHPASS

hudl_tegra_key_path = os.path.expanduser(os.path.join("~", ".ssh", "hudl_tegra_key"))
if len(sys.argv) > 1:
    host = f'ubuntu@{sys.argv[1]}'
else:
    print('Usage python install_devtools.py <ip-address>')
    sys.exit()

connection = Connection(host = host, connect_kwargs = {"key_filename": hudl_tegra_key_path, "password": SSHPASS})
sudopass = Responder(
    pattern=r'\[sudo\] password for ubuntu:',
    response=f'{SUDOPASS}\n'
)
connection.run("sudo apt-get update", pty=True, watchers=[sudopass])
connection.run("sudo apt-get install focus-devtools/stable", pty=True, watchers=[sudopass])