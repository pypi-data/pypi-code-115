# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['extraire']

package_data = \
{'': ['*']}

install_requires = \
['fabric>=2.7.0,<3.0.0', 'pyasn1>=0.4.8,<0.5.0', 'rich>=12.0.1,<13.0.0']

entry_points = \
{'console_scripts': ['extraire = extraire.__main__:main']}

setup_kwargs = {
    'name': 'extraire',
    'version': '0.1.4',
    'description': 'Dumps onboard SHSH blobs with a valid generator for jailbroken iOS devices',
    'long_description': '<h1 align="center">extraire</h1>\n\n<p align="center">\n<a href="https://github.com/beerpiss/extraire/actions"><img alt="Actions Status" src="https://github.com/beerpiss/extraire/actions/workflows/build.yaml/badge.svg"></a>\n<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>\n<a href="https://github.com/beerpiss/extraire/blob/trunk/LICENSE"><img alt="License: 0BSD" src="https://img.shields.io/static/v1?label=License&message=0BSD&color=brightgreen"></a>\n<img alt="Supported Python versions: 3.6.2, 3.7, 3.8, 3.9, 3.10" src="https://img.shields.io/badge/python-3.6.2%20%7C%203.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue">\n</p>\n\n> extraire (verb): to extract\n\nSimple program to dump onboard SHSH blobs with a valid generator for **jailbroken** iOS devices. Supports Windows, macOS and Linux.\n\n## What\'s this?\nThis program dumps the IMG4 ApTicket from /dev/disk1 on the device, copies it to your computer and converts it to a valid SHSH blob, no external dependencies required.\n\nEven though the dumped SHSH blob is valid, you will still be limited by a few factors:\n- SEP/Baseband/Rose firmware compatibility with the currently signed iOS version\n- If you\'ve updated to your current iOS version with the Settings app, you cannot use the dumped blob without a bootROM exploit (e.g. checkm8).\n\n## Requirements\nOpenSSH Server installed on your jailbroken device. That\'s it!\n\n## Installation\n### From PyPI\n```\npip install -U extraire\n```\n### Standalone binaries\nStandalone binaries for Windows, macOS and Linux can be found [here.](https://github.com/beerpiss/extraire/releases/tag/v0.1.4)\n\nYou will need to allow executable permission for macOS and Linux after downloading. Run `chmod +x /path/to/extraire` in a terminal (replace `/path/to/extraire` with the actual path).\n\n## Usage\nRun `extraire` only for an interactive guide.\n\n```\n❯ extraire --help\nusage: extraire [-h] [-p PASSWORD] [-o OUTPUT] [--non-interactive] [HOST[:PORT]]\n\npositional arguments:\n  HOST[:PORT]           The device\'s IP address\n\noptional arguments:\n  -h, --help            show this help message and exit\n  -p PASSWORD, --password PASSWORD\n                        The device\'s root user password\n  -o OUTPUT, --output OUTPUT\n                        Where to save the dumped blob\n  --non-interactive     Don\'t interactively ask for missing value (assume default if missing)\n```\n\n## Ugh, I don\'t like standalone binaries?\nFine. Clone this repo, install the dependencies with `poetry install` or `pip install .`, and run `python3 -m extraire`\n\n## Credits\n[tihmstar](https://github.com/tihmstar): without his [img4tool](https://github.com/tihmstar/img4tool) code I wouldn\'t be able to write code for dealing with IMG4s in Python.\n',
    'author': 'beerpiss',
    'author_email': 'lacvtg.a1.2023@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.6.2,<3.11',
}


setup(**setup_kwargs)
