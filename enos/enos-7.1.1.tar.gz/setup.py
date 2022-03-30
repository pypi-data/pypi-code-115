# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['enos',
 'enos.ansible.plugins.callback',
 'enos.ansible.roles.collectd.files',
 'enos.provider',
 'enos.services',
 'enos.tasks',
 'enos.utils']

package_data = \
{'': ['*'],
 'enos': ['ansible/*',
          'ansible/group_vars/*',
          'ansible/roles/cadvisor/defaults/*',
          'ansible/roles/cadvisor/tasks/*',
          'ansible/roles/collectd/defaults/*',
          'ansible/roles/collectd/tasks/*',
          'ansible/roles/collectd/templates/*',
          'ansible/roles/grafana/defaults/*',
          'ansible/roles/grafana/tasks/*',
          'ansible/roles/influx/defaults/*',
          'ansible/roles/influx/files/*',
          'ansible/roles/influx/tasks/*',
          'ansible/roles/init_os/tasks/*',
          'ansible/roles/init_os/templates/*',
          'resources/*',
          'resources/workload/*',
          'templates/*']}

install_requires = \
['docopt>=0.6.2,<0.7.0',
 'enoslib[chameleon]>=5.6,<5.7',
 'python-heatclient>=2.3.0,<3.0.0',
 'python-openstackclient>=5.5.0,<6.0.0',
 'virtualenv>=20.4.3,<21.0.0']

extras_require = \
{'annotations': ['influxdb==4.0.0']}

entry_points = \
{'console_scripts': ['enos = enos.cli:main']}

setup_kwargs = {
    'name': 'enos',
    'version': '7.1.1',
    'description': 'Experimental eNvironment for OpenStack',
    'long_description': "|Build Status| |Doc Status| |Pypi| |Code style| |License|\n\nJoin us on gitter :  |Join the chat at\nhttps://gitter.im/BeyondTheClouds/enos|\n\nAbout Enos\n==========\n\nEnos aims at reproducible experiments of OpenStack.  Enos relies on\n`Kolla Ansible <https://docs.openstack.org/kolla-ansible/>`__ and\nhelps you to easily deploy, customize and benchmark an OpenStack on\nseveral testbeds including `Grid'5000 <https://www.grid5000.fr>`__,\n`Chameleon <https://www.chameleoncloud.org/>`__ and more generally any\nOpenStack cloud.\n\nInstallation\n============\n\nEnos is best installed via `pip <https://pip.pypa.io/>`__.  It is\ntested with python3.7+::\n\n  pip install enos\n\nQuick Start\n===========\n\nFor the quick-start, we will bring up an OpenStack on VirtualBox.\nVirtualBox is free and works on all major platforms.  Enos can,\nhowever, work with many testbeds including `Grid'5000\n<https://beyondtheclouds.github.io/enos/provider/grid5000.html>`__ and\n`Chameleon\n<https://beyondtheclouds.github.io/enos/provider/openstack.html>`__.\n\nFirst, make sure your development machine has `VirtualBox\n<https://www.virtualbox.org/>`__ and `Vagrant\n<https://www.vagrantup.com/downloads>`__ installed.  Then, ensure that\nyou have at least 10 GiB of memory.\n\nTo deploy your fist OpenStack with enos::\n\n  enos new --provider=vagrant:virtualbox  # Generate a `reservation.yaml` file\n  enos deploy\n\nEnos starts three virtual machines and configures Kolla Ansible to\ndeploy the OpenStack control plane on the first one, the network\nrelated services (Neutron, HAProxy, RabbitMQ) on the second one, and\nuse the last one as a compute node.  Note that the full deployment may\ntake a while (around 30 minutes to pull and run all OpenStack docker\nimages).\n\nYou can `customize\n<https://beyondtheclouds.github.io/enos/customization/>`__ the\ndeployed services and the number of virtual machines allocated by\nmodifying the generated ``reservation.yaml`` file.  Calls ``enos\n--help`` or read the `documentation\n<https://beyondtheclouds.github.io/enos/>`__ for more information.\n\nAcknowledgment\n==============\n\nEnos is developed in the context of the `Discovery\n<https://beyondtheclouds.github.io/>`__ initiative.\n\n\nLinks\n=====\n\n-  Docs - https://beyondtheclouds.github.io/enos/\n-  Discovery - https://beyondtheclouds.github.io/\n-  Docker - https://hub.docker.com/r/beyondtheclouds/\n\n.. |Build Status| image:: https://travis-ci.org/BeyondTheClouds/enos.svg?branch=master\n   :target: https://travis-ci.org/BeyondTheClouds/enos\n.. |Join the chat at https://gitter.im/BeyondTheClouds/enos| image:: https://badges.gitter.im/BeyondTheClouds/enos.svg\n   :target: https://gitter.im/BeyondTheClouds/enos?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge\n.. |Code style| image:: https://api.codacy.com/project/badge/Grade/87536e9c0f0d47e08d1b9e0950c9d14b\n   :target: https://www.codacy.com/app/msimonin/enos?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=BeyondTheClouds/enos&amp;utm_campaign=Badge_Grade\n.. |License| image:: https://img.shields.io/badge/License-GPL%20v3-blue.svg\n   :target: https://www.gnu.org/licenses/gpl-3.0\n.. |Pypi| image:: https://badge.fury.io/py/enos.svg\n    :target: https://badge.fury.io/py/enos\n.. |Doc Status| image:: https://github.com/BeyondTheClouds/enos/actions/workflows/build-and-publish-doc.yml/badge.svg\n   :target: https://github.com/BeyondTheClouds/enos/actions/workflows/build-and-publish-doc.yml\n",
    'author': 'Didier Iscovery',
    'author_email': 'discovery-dev@inria.fr',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/BeyondTheClouds/enos',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
