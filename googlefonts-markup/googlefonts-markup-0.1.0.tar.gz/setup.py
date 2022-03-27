# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['googlefonts_markup']

package_data = \
{'': ['*']}

install_requires = \
['pydantic']

setup_kwargs = {
    'name': 'googlefonts-markup',
    'version': '0.1.0',
    'description': 'Small utility to use Google Fonts for markup files',
    'long_description': '==================\ngooglefonts-markup\n==================\n\n.. warning:: This is alpha library\n\nOverview\n========\n\nThis is small utility to handle specs of Google Fonts in my products.\n\nUsage\n=====\n\n.. note:: WIP\n\nSimple case\n-----------\n\n.. code-block:: python\n\n   >>> from googlefonts_markup import Font\n   >>> noto_sans_jp = Font(family_name="Noto Sans JP")\n   >>> noto_sans_jp.css_url()\n   \'https://fonts.googleapis.com/css2?family=Noto+Sans+JP\'\n   >>> noto_sans_jp.css_tag()\n   \'<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP" rel="stylesheet">\'\n\nIf you want only URL of CSS, use ``googlefonts_markup.shortcuts``.\n\n.. code-block:: python\n\n   >>> from googlefonts_markup.shortcuts import font_css_url\n   >>> font_css_url("Noto Sans JP")\n   \'https://fonts.googleapis.com/css2?family=Noto+Sans+JP\'\n\nWith italic\n-----------\n\n.. code-block:: python\n\n   >>> from googlefonts_markup import Axis, Font\n   >>> red_hat_mono = Font(family_name="Red Hat Mono", axis_list=[Axis(italic=True)])\n   >>> red_hat_mono.css_url()\n   \'https://fonts.googleapis.com/css2?family=Red+Hat+Mono:ital,wght@1,400\'\n\nExtra attributes\n----------------\n\n.. code-block:: python\n\n   >>> from googlefonts_markup import Font, FontSet\n   >>> noto_sans_jp = Font(family_name="Noto Sans JP")\n   >>> fontset = FontSet(fonts=[noto_sans_jp], display="swap")\n   >>> fontset.css_url()\n   \'https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap\'\n\nMultiple fonts\n--------------\n\n.. code-block:: python\n\n   >>> from googlefonts_markup import Font, FontSet\n   >>> noto_sans_jp = Font(family_name="Noto Sans JP")\n   >>> roboto_mono = Font(family_name="Roboto Mono")\n   >>> fontset = FontSet(fonts=[noto_sans_jp, roboto_mono], display="swap")\n   >>> fontset.css_url()\n   \'https://fonts.googleapis.com/css2?family=Noto+Sans+JP&family=Roboto+Mono&display=swap\'\n\nInstallation\n============\n\n.. code-block:: console\n\n   pip install git+https://github.com/attakei-lab/googlefonts-markup\n',
    'author': 'Kazuya Takei',
    'author_email': 'myself@attakei.net',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
