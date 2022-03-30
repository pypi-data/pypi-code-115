# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['strapi_client']

package_data = \
{'': ['*']}

install_requires = \
['requests']

setup_kwargs = {
    'name': 'strapi-client',
    'version': '1.0.0',
    'description': 'Work with Strapi from Python via REST API',
    'long_description': "# Strapi Client\n\nWork with Strapi from Python via REST API\n\n## Install\n\n```bash\npip install strapi-client\n```\n\n## Documentation\n\n[Full API Reference](./docs)\n\n## Examples\n\nQuick start:\n\n```python\nfrom strapi_client import StrapiClient\n\nstrapi = StrapiClient(strapi_url)\nstrapi.authorize(your_identifier, your_password) # optional\nusers = strapi.get_entries('users', filters={'username': {'$eq': 'Pavel'}})\nuser_id = users['data'][0]['id']\nstrapi.update_entry('users', user_id, data={'username': 'Mark'})\n```\n\n## Development\n\n### Create new release\n\nPush changes to 'main' branch following [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).\n\n### Update documentation\n\n`docs` folder is being updated automatically by GitHub Actions when source files are changed.\n",
    'author': 'Pavel Roslovets',
    'author_email': 'p.v.roslovets@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/Roslovets-Inc/strapi-client',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6',
}


setup(**setup_kwargs)
