# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['dude', 'dude.optional']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=6.0,<7.0', 'braveblock>=0.1.13,<0.3.0', 'playwright>=1.19.0,<2.0.0']

extras_require = \
{'bs4': ['beautifulsoup4>=4.10.0,<5.0.0', 'httpx>=0.22.0,<0.23.0'],
 'lxml': ['cssselect>=1.1.0,<2.0.0',
          'httpx>=0.22.0,<0.23.0',
          'lxml>=4.8.0,<5.0.0'],
 'parsel': ['httpx>=0.22.0,<0.23.0', 'parsel>=1.6.0,<2.0.0'],
 'pyppeteer': ['pyppeteer>=1.0.2,<2.0.0'],
 'selenium': ['selenium-wire>=4.6.2,<5.0.0', 'webdriver-manager>=3.5.3,<4.0.0']}

entry_points = \
{'console_scripts': ['dude = dude:cli']}

setup_kwargs = {
    'name': 'pydude',
    'version': '0.12.2',
    'description': 'dude uncomplicated data extraction',
    'long_description': '<table>\n    <tr>\n        <td>License</td>\n        <td><img src=\'https://img.shields.io/pypi/l/pydude.svg?style=for-the-badge\' alt="License"></td>\n        <td>Version</td>\n        <td><img src=\'https://img.shields.io/pypi/v/pydude.svg?logo=pypi&style=for-the-badge\' alt="Version"></td>\n    </tr>\n    <tr>\n        <td>Github Actions</td>\n        <td><img src=\'https://img.shields.io/github/workflow/status/roniemartinez/dude/Python?label=actions&logo=github%20actions&style=for-the-badge\' alt="Github Actions"></td>\n        <td>Coverage</td>\n        <td><img src=\'https://img.shields.io/codecov/c/github/roniemartinez/dude/branch?label=codecov&logo=codecov&style=for-the-badge\' alt="CodeCov"></td>\n    </tr>\n    <tr>\n        <td>Supported versions</td>\n        <td><img src=\'https://img.shields.io/pypi/pyversions/pydude.svg?logo=python&style=for-the-badge\' alt="Python Versions"></td>\n        <td>Wheel</td>\n        <td><img src=\'https://img.shields.io/pypi/wheel/pydude.svg?style=for-the-badge\' alt="Wheel"></td>\n    </tr>\n    <tr>\n        <td>Status</td>\n        <td><img src=\'https://img.shields.io/pypi/status/pydude.svg?style=for-the-badge\' alt="Status"></td>\n        <td>Downloads</td>\n        <td><img src=\'https://img.shields.io/pypi/dm/pydude.svg?style=for-the-badge\' alt="Downloads"></td>\n    </tr>\n</table>\n\n# dude uncomplicated data extraction\n\nDude is a very simple framework for writing web scrapers using Python decorators.\nThe design, inspired by [Flask](https://github.com/pallets/flask), was to easily build a web scraper in just a few lines of code.\nDude has an easy-to-learn syntax.\n\n> 🚨 Dude is currently in Pre-Alpha. Please expect breaking changes.\n\n## Installation\n\nTo install, simply run the following from terminal.\n\n```bash\npip install pydude\nplaywright install  # Install playwright binaries for Chrome, Firefox and Webkit.\n```\n\n## Minimal web scraper\n\nThe simplest web scraper will look like this:\n\n```python\nfrom dude import select\n\n\n@select(css="a")\ndef get_link(element):\n    return {"url": element.get_attribute("href")}\n```\n\nThe example above will get all the [hyperlink](https://en.wikipedia.org/wiki/Hyperlink#HTML) elements in a page and calls the handler function `get_link()` for each element.\n\n## How to run the scraper\n\nYou can run your scraper from terminal/shell/command-line by supplying URLs, the output filename of your choice and the paths to your python scripts to `dude scrape` command.\n\n```bash\ndude scrape --url "<url>" --output data.json path/to/script.py\n```\n\nThe output in `data.json` should contain the actual URL and the metadata prepended with underscore.\n\n```json5\n[\n  {\n    "_page_number": 1,\n    "_page_url": "https://dude.ron.sh/",\n    "_group_id": 4502003824,\n    "_group_index": 0,\n    "_element_index": 0,\n    "url": "/url-1.html"\n  },\n  {\n    "_page_number": 1,\n    "_page_url": "https://dude.ron.sh/",\n    "_group_id": 4502003824,\n    "_group_index": 0,\n    "_element_index": 1,\n    "url": "/url-2.html"\n  },\n  {\n    "_page_number": 1,\n    "_page_url": "https://dude.ron.sh/",\n    "_group_id": 4502003824,\n    "_group_index": 0,\n    "_element_index": 2,\n    "url": "/url-3.html"\n  }\n]\n```\n\nChanging the output to `--output data.csv` should result in the following CSV content.\n\n![data.csv](docs/csv.png)\n\n## Features\n\n- Simple [Flask](https://github.com/pallets/flask)-inspired design - build a scraper with decorators.\n- Uses [Playwright](https://playwright.dev/python/) API - run your scraper in Chrome, Firefox and Webkit and leverage Playwright\'s powerful selector engine supporting CSS, XPath, text, regex, etc.\n- Data grouping - group related results.\n- URL pattern matching - run functions on specific URLs.\n- Priority - reorder functions based on priority.\n- Setup function - enable setup steps (clicking dialogs or login).\n- Navigate function - enable navigation steps to move to other pages.\n- Custom storage - option to save data to other formats or database.\n- Async support - write async handlers.\n- Option to use other parser backends aside from Playwright.\n  - [BeautifulSoup4](https://roniemartinez.github.io/dude/advanced/09_beautifulsoup4.html) - `pip install pydude[bs4]`\n  - [Parsel](https://roniemartinez.github.io/dude/advanced/10_parsel.html) - `pip install pydude[parsel]`\n  - [lxml](https://roniemartinez.github.io/dude/advanced/11_lxml.html) - `pip install pydude[lxml]`\n  - [Pyppeteer](https://roniemartinez.github.io/dude/advanced/12_pyppeteer.html) - `pip install pydude[pyppeteer]`\n  - [Selenium](https://roniemartinez.github.io/dude/advanced/13_selenium.html) - `pip install pydude[selenium]`\n- Option to follow all links indefinitely (Crawler/Spider).\n- Events - attach functions to startup, pre-setup, post-setup and shutdown events.\n- Option to save data on every page.\n\n## Supported Parser Backends\n\nBy default, Dude uses Playwright but gives you an option to use parser backends that you are familiar with.\nIt is possible to use parser backends like \n[BeautifulSoup4](https://roniemartinez.github.io/dude/advanced/09_beautifulsoup4.html), \n[Parsel](https://roniemartinez.github.io/dude/advanced/10_parsel.html),\n[lxml](https://roniemartinez.github.io/dude/advanced/11_lxml.html),\n[Pyppeteer](https://roniemartinez.github.io/dude/advanced/12_pyppeteer.html), \nand [Selenium](https://roniemartinez.github.io/dude/advanced/13_selenium.html).\n\nHere is the summary of features supported by each parser backend.\n\n<table>\n<thead>\n  <tr>\n    <td rowspan="2" style=\'text-align:center;\'>Parser Backend</td>\n    <td rowspan="2" style=\'text-align:center;\'>Supports<br>Sync?</td>\n    <td rowspan="2" style=\'text-align:center;\'>Supports<br>Async?</td>\n    <td colspan="4" style=\'text-align:center;\'>Selectors</td>\n    <td rowspan="2" style=\'text-align:center;\'><a href="https://roniemartinez.github.io/dude/advanced/01_setup.html">Setup<br>Handler</a></td>\n    <td rowspan="2" style=\'text-align:center;\'><a href="https://roniemartinez.github.io/dude/advanced/02_navigate.html">Navigate<br>Handler</a></td>\n  </tr>\n  <tr>\n    <td>CSS</td>\n    <td>XPath</td>\n    <td>Text</td>\n    <td>Regex</td>\n  </tr>\n</thead>\n<tbody>\n  <tr>\n    <td>Playwright</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n  </tr>\n  <tr>\n    <td>BeautifulSoup4</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>🚫</td>\n    <td>🚫</td>\n    <td>🚫</td>\n    <td>🚫</td>\n    <td>🚫</td>\n  </tr>\n  <tr>\n    <td>Parsel</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>🚫</td>\n    <td>🚫</td>\n  </tr>\n  <tr>\n    <td>lxml</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>🚫</td>\n    <td>🚫</td>\n  </tr>\n  <tr>\n    <td>Pyppeteer</td>\n    <td>🚫</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>🚫</td>\n    <td>✅</td>\n    <td>✅</td>\n  </tr>\n  <tr>\n    <td>Selenium</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>✅</td>\n    <td>🚫</td>\n    <td>✅</td>\n    <td>✅</td>\n  </tr>\n</tbody>\n</table>\n\n## Documentation\n\nRead the complete documentation at [https://roniemartinez.github.io/dude/](https://roniemartinez.github.io/dude/).\nAll the advanced and useful features are documented there.\n\n## Requirements\n\n- ✅ Any dude should know how to work with selectors (CSS or XPath).\n- ✅ Familiarity with any backends that you love (see [Supported Parser Backends](#supported-parser-backends))\n- ✅ Python decorators... you\'ll live, dude!\n\n## Why name this project "dude"?\n\n- ✅ A [Recursive acronym](https://en.wikipedia.org/wiki/Recursive_acronym) looks nice.\n- ✅ Adding "uncomplicated" (like [`ufw`](https://wiki.ubuntu.com/UncomplicatedFirewall)) into the name says it is a very simple framework. \n- ✅ Puns! I also think that if you want to do web scraping, there\'s probably some random dude around the corner who can make it very easy for you to start with it. 😊\n\n## Author\n\n[Ronie Martinez](mailto:ronmarti18@gmail.com)\n',
    'author': 'Ronie Martinez',
    'author_email': 'ronmarti18@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/roniemartinez/dude',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
