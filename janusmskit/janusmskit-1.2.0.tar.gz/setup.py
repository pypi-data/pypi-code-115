# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['janusmskit',
 'janusmskit.cloud.aws',
 'janusmskit.cmd',
 'janusmskit.config',
 'janusmskit.crypt',
 'janusmskit.flask',
 'janusmskit.flask.app',
 'janusmskit.flask.configreload',
 'janusmskit.flask.healthcheck',
 'janusmskit.flask.services',
 'janusmskit.logger',
 'janusmskit.utils']

package_data = \
{'': ['*']}

install_requires = \
['anyconfig>=0.10.1',
 'cryptography>=3.4.7',
 'flask>=1.1.4',
 'python-json-logger>=2.0.0',
 'pyyaml>=5.3.1']

extras_require = \
{'requests': ['requests>=2.26.0,<3.0.0']}

setup_kwargs = {
    'name': 'janusmskit',
    'version': '1.2.0',
    'description': 'Library of utils to create REST Python Microservices',
    'long_description': '# Python Microservices Library\n\n[![PyPI version](https://badge.fury.io/py/py-ms.svg)](https://badge.fury.io/py/py-ms)\n[![Build Status](https://travis-ci.org/python-microservices/pyms.svg?branch=master)](https://travis-ci.org/python-microservices/pyms)\n[![Coverage Status](https://coveralls.io/repos/github/python-microservices/pyms/badge.svg?branch=master)](https://coveralls.io/github/python-microservices/pyms?branch=master)\n[![Requirements Status](https://requires.io/github/python-microservices/pyms/requirements.svg?branch=master)](https://requires.io/github/python-microservices/pyms/requirements/?branch=master)\n[![Total alerts](https://img.shields.io/lgtm/alerts/g/python-microservices/pyms.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/python-microservices/pyms/alerts/)\n[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/python-microservices/pyms.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/python-microservices/pyms/context:python)\n[![Documentation Status](https://readthedocs.org/projects/py-ms/badge/?version=latest)](https://python-microservices.github.io/home/)\n[![Gitter](https://img.shields.io/gitter/room/DAVFoundation/DAV-Contributors.svg)](https://gitter.im/python-microservices/pyms)\n\nPyMS, Python MicroService, is a [Microservice chassis pattern](https://microservices.io/patterns/microservice-chassis.html)\nlike Spring Boot (Java) or Gizmo (Golang). PyMS is a collection of libraries, best practices and recommended ways to build\nmicroservices with Python which handles cross-cutting concerns:\n\n- Externalized configuration\n- Logging\n- Health checks\n- Metrics\n- Distributed tracing\n\nPyMS is powered by [Flask](https://flask.palletsprojects.com/en/1.1.x/), [Connexion](https://github.com/zalando/connexion)\nand [Opentracing](https://opentracing.io/).\n\nGet started with [Installation](https://python-microservices.github.io/installation/)\nand then get an overview with the [Quickstart](https://python-microservices.github.io/quickstart/).\n\n## Documentation\n\nTo know how to use, install or build a project see the [docs](https://python-microservices.github.io/).\n\n## Installation\n\n```bash\npip install py-ms[all]\n```\n\n## Quickstart\n\nSee our [quickstart webpage](https://python-microservices.github.io/quickstart/)\n\n## Create a project from scaffold\n\nSee our [Create a project from scaffold webpage](https://python-microservices.github.io/quickstart/#create-a-project-from-scaffold)\n\n## How To contribute\n\nWe appreciate opening issues and pull requests to make PyMS even more stable & useful! See [This doc](https://python-microservices.github.io/contributing/)\nfor more details.\n',
    'author': 'avara1986',
    'author_email': 'a.vara.1986@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://python-microservices.github.io/',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'python_requires': '>=3.6.1,<4.0',
}


setup(**setup_kwargs)
