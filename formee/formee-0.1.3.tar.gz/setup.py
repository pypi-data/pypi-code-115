# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['formee', 'formee.auth', 'formee.formTools']

package_data = \
{'': ['*']}

install_requires = \
['PyInquirer>=1.0.3,<2.0.0',
 'PyYAML>=6.0,<7.0',
 'aiohttp>=3.8.1,<4.0.0',
 'gql>=3.1.0,<4.0.0',
 'pyfiglet>=0.8.post1,<0.9',
 'python-dotenv>=0.20.0,<0.21.0',
 'requests>=2.27.1,<3.0.0',
 'rich>=12.0.1,<13.0.0']

entry_points = \
{'console_scripts': ['formee = formee.__main__:main']}

setup_kwargs = {
    'name': 'formee',
    'version': '0.1.3',
    'description': 'Formee is a tool that provides an easy way to create, edit and manage all of your forms from the command line. It uses a powerful GraphQL API and strives to make the process of working with forms as easy and simple as possible.',
    'long_description': "\n# Formee- The terminal forms\n\nFormee is a tool that provides an easy way to create, edit and manage all of your forms from the command line. It uses a powerful GraphQL API and strives to make the process of working with forms as easy and simple as possible.\n\n![Formee Logo](docs/docs_assets/images/logo.svg)\n\n\n## Badges\n\n[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/Arpan-206/formee/blob/main/LICENSE)\n[![Python 3.8 or above](https://img.shields.io/badge/python-%5E3.8-blue)](https://python.org/)\n[![Hasura](https://img.shields.io/badge/Built%20With-Hasura-yellowgreen)](https://hasura.io)\n\n\n## Installation\n\n1. Install *formee* with pip\n\n```bash\npip3 install formee\n```\n\n2. Use the Github repository\n\n    ```bash\n    git clone https://github.com/Arpan-206/formee.git\n    cd formee\n    ```\n\n    - If you use poetry, then:\n        ```bash\n        poetry install\n        ```\n    - Otherwise, use pip\n        ```bash\n        pip3 install -r requirements.txt\n        ```\n\n## Usage\n\n1. [Install the CLI.](#Installation)\n2. Run the command\n```bash\npython3 -m formee\n```\n3. You're good to go.\n## Documentation\nAccess the Documentation over \n[here](https://linktodocumentation).\n\n\n## License\n\n[MIT](https://github.com/Arpan-206/formee/blob/main/LICENSE)\n\n\n\n## Roadmap\n\n- Add more type of fields\n\n- Work on security\n\n- Work on Auth\n\n- Improve WebUI\n\n- Improve runtime\n\n\n## Authors\n\n- [@Arpan-206](https://github.com/Arpan-206)\n\n\n## Feedback\n\nIf you have any feedback, please reach out to us at arpan@hackersreboot.tech.\n\n\n## Contributing\n\nContributions are always welcome!\n\nSee `contributing.md` for ways to get started.\n\nPlease adhere to this project's `code of conduct`.\n\n",
    'author': 'Arpan Pandey',
    'author_email': 'arpan@hackersreboot.tech',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/Arpan-206/formee',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
