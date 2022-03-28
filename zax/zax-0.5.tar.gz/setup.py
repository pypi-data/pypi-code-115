# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['zax', 'zax.formats', 'zax.icons', 'zax.images', 'zax.layouts']

package_data = \
{'': ['*']}

install_requires = \
['PySimpleGUIQt>=0.35.0',
 'appdirs>=1.4.3',
 'cssutils>=2.3.0',
 'iniparse>=0.5',
 'loguru>=0.5.3',
 'packaging>=20.4',
 'pefile>=2021.9.3',
 'py7zr>=0.16.3',
 'requests>=2.22.0',
 'ruamel.yaml>=0.16.10']

entry_points = \
{'console_scripts': ['zax = zax.__main__:main']}

setup_kwargs = {
    'name': 'zax',
    'version': '0.5',
    'description': 'ZAX',
    'long_description': '# ZAX\n[![Build status](https://github.com/BGforgeNet/ZAX/workflows/build/badge.svg)](https://github.com/BGforgeNet/ZAX/actions?query=workflow%3Abuild) <a href="#"><img align="right" src="https://raw.githubusercontent.com/BGforgeNet/zax/master/docs/zax.png" width="45%" alt="ZAX screenshot" title="ZAX screenshot"/></a>\n[![Patreon](https://img.shields.io/badge/Patreon-donate-FF424D?logo=Patreon&labelColor=141518)](https://www.patreon.com/BGforge)\n\n[![Telegram](https://img.shields.io/badge/telegram-join%20%20%20%20%E2%9D%B1%E2%9D%B1%E2%9D%B1-darkorange?logo=telegram)](https://t.me/bgforge)\n[![Discord](https://img.shields.io/discord/420268540700917760?logo=discord&label=discord&color=blue&logoColor=FEE75C)](https://discord.gg/4Yqfggm)\n[![IRC](https://img.shields.io/badge/%23IRC-join%20%20%20%20%E2%9D%B1%E2%9D%B1%E2%9D%B1-darkorange)](https://bgforge.net/irc)\n\n\nZAX is a Fallout 2 game manager. Its purpose is to unify and simplify game and mods configuration. It should work with any game based on Fallout 2 engine.\n\n### Installation\n\n#### Windows\nDownload `zax.exe` from the [latest release page](https://github.com/BGforgeNet/zax/releases/latest) and launch it.\n\n#### Linux / Mac / other\n- There\'s a x64 [binary](https://github.com/BGforgeNet/zax/releases/latest) for Linux.\n- ZAX is also available in PyPi:\n    ```bash\n    pip3 install zax\n    zax\n    ```\n\n### Info\n- [Forums](https://forums.bgforge.net/viewforum.php?f=34)\n- [Development](docs/development.md)\n- [Changelog](docs/changelog.md)\n',
    'author': 'BGforge',
    'author_email': 'dev@bgforge.net',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/BGforgeNet/zax',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<3.11',
}


setup(**setup_kwargs)
