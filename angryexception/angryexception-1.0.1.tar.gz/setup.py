# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['angryexception']

package_data = \
{'': ['*']}

install_requires = \
['pyttsx3>=2.90,<3.0']

setup_kwargs = {
    'name': 'angryexception',
    'version': '1.0.1',
    'description': "An exception handler that tells you that you're stupid.",
    'long_description': "# angryexception\n\nAn exception handler that tells you that you're stupid.\n\n## Installation\n\n`pip install angryexception`\n\nYou will also need to have either libespeak, sapi5, or nsss speech engines installed.\n\n## Usage\n\n```py\nfrom angryexception import install\n\ninstall()\n\n# Create an exception\nraise Exception()\n```\n",
    'author': 'vcokltfre',
    'author_email': 'vcokltfre@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/vcokltfre/angryexception',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)
