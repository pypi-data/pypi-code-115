# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['ab_nic_sw']

package_data = \
{'': ['*']}

install_requires = \
['dpkt>=1.9.7,<2.0.0',
 'fxpmath>=0.4.5,<0.5.0',
 'rich>=12.0.1,<13.0.0',
 'scapy>=2.4.5,<3.0.0',
 'ska-low-cbf-fpga>=0.12.0,<0.13.0']

entry_points = \
{'console_scripts': ['change_port = ab_nic_sw.change_port:main',
                     'compare_pcap = ab_nic_sw.compare_pcap:main',
                     'eth_interface_rate = ab_nic_sw.eth_interface_rate:main',
                     'pcap_to_hbm = ab_nic_sw.pcap_to_hbm:main']}

setup_kwargs = {
    'name': 'ab-nic-sw',
    'version': '0.2.1',
    'description': 'Alveo Burst NIC Control Software',
    'long_description': None,
    'author': 'Andrew Bolin, Jason van Aardt, CSIRO',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
