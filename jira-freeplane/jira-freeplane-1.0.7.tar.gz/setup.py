# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['jira_freeplane']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=5.4.1,<7',
 'jira>=3.1.1,<4',
 'untangle>=1.1.1,<2',
 'urllib3>=1.26.5,<2']

entry_points = \
{'console_scripts': ['jira-freeplane = '
                     'jira_freeplane.runtime:run_mindmap_to_jira']}

setup_kwargs = {
    'name': 'jira-freeplane',
    'version': '1.0.7',
    'description': 'Make JIRA Epics, Tasks, and Sub-tasks via a freeplane mindmap',
    'long_description': 'JIRA Freeplane issue creator\n=============================\n\n.. contents:: Page Contents\n\n.. image:: http://unmaintained.tech/badge.svg\n  :target: http://unmaintained.tech\n  :alt: No Maintenance Intended\n\n\nLong Description\n\n\nInstallation\n------------\n\n.. code:: bash\n\n    pip install jira_freeplane\n\n\nContribute\n----------\n\n- Issue Tracker: github.com/shollingsworth/$project/issues\n- Source Code: github.com/shollingsworth/$project\n\nSupport\n-------\n\nUnfortunately, there is no support for this project. We do welcome\ncontributions and pull requests though!\n\n\nLicense\n-------\n\nThe project is licensed under the MIT license.\nsee `LICENSE <https://github.com/shollingsworth/jira-freeplane/blob/main/LICENSE.txt>`_\n',
    'author': 'Stevo',
    'author_email': 'hollingsworth.stevend@gmail.com',
    'maintainer': 'Stevo',
    'maintainer_email': 'hollingsworth.stevend@gmail.com',
    'url': 'https://github.com/shollingsworth/jira-freeplane',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4',
}


setup(**setup_kwargs)
