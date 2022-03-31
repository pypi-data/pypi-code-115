import socket
from time import sleep
from yaspin import yaspin
import nmap
import os
import argparse

parser = argparse.ArgumentParser(description="search for pi's in your LAN")
parser.add_argument('-c', action='store_true',
                    help='continuous scanning')

args = parser.parse_args()

logo = """

   .~~.   .~~.
  '. \ ' ' / .'
   .~ .~~~..~.
  : .~.'~'.~. :
 ~ (   ) (   ) ~
( : '~'.~.'~' : )
 ~ .~ (   ) ~. ~
  (  : '~' :  ) Raspberry Pi finder
   '~ .~~~. ~'
       '~'


       
"""


def is_root():
    return os.geteuid() == 0


def get_myIP():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        st.close()
    return IP


def run():

    if not is_root():
        print("root priv needed, exiting")
        exit()

    print(logo)

    hosts = '.'.join(get_myIP().split('.')[:3]) + '.0/24'

    target_prefixes = ["DC:A6:32",
                       "E4:5F:01",
                       "B8:27:EB", ]

    nm = nmap.PortScanner()

    while True:
        found = {}

        with yaspin() as sp:
            sp.text = "running nmap..."
            nm.scan(hosts=hosts, arguments='-sP')

        host_list = nm.all_hosts()

        for host in host_list:
            if 'mac' in nm[host]['addresses']:
                for target_prefix in target_prefixes:
                    if target_prefix in nm[host]['addresses']['mac']:
                        found.update({host: nm[host]['addresses']['mac']})

        if len(found) == 0:
            print("No results")
            print("Sleeping...")
            sleep(8)
        else:
            for host, mac in found.items():
                print(
                    f"📍 {host} is a raspberry pi [{mac}] | ssh://pi@{host} or 'ssh pi@{host}'")
            if not args.c:
                break
            else:
                print("Sleeping...")
                sleep(8)
