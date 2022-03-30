# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['regta']

package_data = \
{'': ['*'], 'regta': ['templates/*']}

install_requires = \
['Jinja2>=3.0.3,<4.0.0', 'asyncio>=3.4.3,<4.0.0', 'click>=8.0.3,<9.0.0']

entry_points = \
{'console_scripts': ['regta = regta.console:main']}

setup_kwargs = {
    'name': 'regta',
    'version': '0.2.0',
    'description': 'Lightweight framework for executing periodic async and sync jobs in python',
    'long_description': '# regta\n**Lightweight framework to create and execute periodic async and sync jobs on \ndifferent processes, threads and event loop.**\n\n[![pypi](https://img.shields.io/pypi/v/regta.svg)](https://pypi.python.org/pypi/regta)\n[![versions](https://img.shields.io/pypi/pyversions/regta.svg)](https://github.com/SKY-ALIN/regta)\n[![license](https://img.shields.io/github/license/SKY-ALIN/regta.svg)](https://github.com/SKY-ALIN/regta/blob/main/LICENSE)\n\n### Core Features\n\n- **Different Jobs** - Create async, thread-based or process-based jobs \n  depending on your goals.\n\n\n- **Support different code styles** - Create OOP styled or functional styled \n  jobs. Regta also provide interface to reuse user\'s already written code.\n\n\n- **CLI interface to work with jobs** - Regta provide CLI tool to list and \n  start available written jobs.\n\n\n- **Logging** - Redefine standard and define your own logging way.\n\n---\n\n### Installation\nInstall using `pip install regta` or `poetry add regta`. \nYou can check if **regta** was installed correctly with the following \ncommand `regta --help`.\n\n### Example\nTo write async job use `@regta.async_job()` decorator\n```python\n# jobs/some_async_job.py\n\nfrom datetime import timedelta\nimport regta\n\n@regta.async_job(interval=timedelta(seconds=5))\nasync def my_basic_job():\n    return "Hello world! This is just a log message."\n```\nSee more about different jobs types \n[here](https://regta.alinsky.tech/user_guide/make_jobs).\n\n### Start Up\nTo start jobs use `regta run` command:\n```shell\n$ regta run\n> [1] jobs were found.\n> jobs.some_async_job:my_basic_job - Hello world! This is just a log message.\n.  .  .\n```\nSee CLI reference [here](https://regta.alinsky.tech/cli_reference).\n\n---\n\nFull documentation and reference is available at \n[regta.alinsky.tech](https://regta.alinsky.tech)\n',
    'author': 'Vladimir Alinsky',
    'author_email': 'Vladimir@Alinsky.tech',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/SKY-ALIN/regta',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
