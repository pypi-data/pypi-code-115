# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['thirdweb',
 'thirdweb.abi',
 'thirdweb.abi.token_erc1155',
 'thirdweb.abi.token_erc20',
 'thirdweb.abi.token_erc721',
 'thirdweb.common',
 'thirdweb.constants',
 'thirdweb.contracts',
 'thirdweb.core',
 'thirdweb.core.classes',
 'thirdweb.core.helpers',
 'thirdweb.types',
 'thirdweb.types.settings']

package_data = \
{'': ['*']}

install_requires = \
['dacite>=1.6.0,<2.0.0',
 'mypy-extensions>=0.4.3,<0.5.0',
 'thirdweb-contract-wrappers>=2.0.4,<3.0.0',
 'web3==5.27.0']

setup_kwargs = {
    'name': 'thirdweb-sdk',
    'version': '2.0.0a2',
    'description': '',
    'long_description': None,
    'author': 'thirdweb',
    'author_email': 'sdk@thirdweb.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>3.7.1,<3.10',
}


setup(**setup_kwargs)
