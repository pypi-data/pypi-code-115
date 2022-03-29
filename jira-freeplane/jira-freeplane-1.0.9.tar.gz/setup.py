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
 'simple-term-menu<=1.4.1',
 'untangle>=1.1.1,<2',
 'urllib3>=1.26.5,<2']

entry_points = \
{'console_scripts': ['jira-freeplane = '
                     'jira_freeplane.runtime:run_mindmap_to_jira']}

setup_kwargs = {
    'name': 'jira-freeplane',
    'version': '1.0.9',
    'description': 'Make JIRA Epics, Tasks, and Sub-tasks via a freeplane mindmap',
    'long_description': 'JIRA Freeplane issue creator\n=============================\n\n.. contents:: Page Contents\n\nSoftware Requirements\n---------------------\n- `Freeplane <http://freeplane.sourceforge.net/>`_\n- Pick one\n    - `Python <http://www.python.org/>`_\n    - `Docker <https://www.docker.com/>`_\n\n\nInstallation\n------------\n\nPython\n^^^^^^\n.. code:: bash\n\n    pip install jira_freeplane\n\nDocker - `jira-freeplane <https://hub.docker.com/r/hollingsworthsteven/jira-freeplane/>`_\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\n.. code:: bash\n\n    docker pull hollingsworthsteven/jira-freeplane\n\nQuickstart\n----------\n\n- Create a new mindmap, see `sample.mm <https://github.com/shollingsworth/jira-freeplane/blob/main/examples/sample.mm>`_ \n  as an example.\n\n\ndocker (interactive mode)\n^^^^^^^^^^^^^^^^^^^^^^^^^\n\n.. tip:: \n\n    This assumes you are running bash or zsh as your shell\n\n    Replace ``$mindmap`` with the file name / path of your mindmap.\n\n    Replace ``$JIRA_USER``, and ``$JIRA_PASS`` with your JIRA credentials.\n\n    (You can also use environment variables if you do not want them to show in\n    your command history)\n\n    do not change ``/config/freeplane_doc.mm`` only ``$mindmap``\n\n.. code:: bash\n\n    docker run --rm -it -v "$(pwd):/app" -v "$mindmap:/config/freeplane_doc.mm" -e "JIRA_USER=${JIRA_USER}" -e "JIRA_PASS=${JIRA_PASS}" -u "$(id -u):$(id -g)" hollingsworthsteven/jira-freeplane jira-freeplane --interactive /config/freeplane_doc.mm\n\n\npython/pip\n^^^^^^^^^^\n\n.. tip:: \n\n   replace\n\n   ``<your_jira_username>``\n\n   and\n\n   ``<your_jira_password>``\n\n   with your JIRA credentials.\n\n.. code:: bash\n\n    pip install jira_freeplane\n    export JIRA_USER=<your_jira_username>\n    export JIRA_PASS=<your_jira_password>\n    jira-freeplane -i /path/to/mindmap.mm\n\n\nContribute\n----------\nPull requests are welcome!\n\n- `Issue Tracker <https://github.com/shollingsworth/jira-freeplane/issues>`_\n- `Source Code <github.com/shollingsworth/jira-freeplane>`_\n\nSupport\n-------\n\nUnfortunately, there is no support for this project. We do welcome\ncontributions and pull requests though!\n\n\nLicense\n-------\n\nThe project is licensed under the MIT license.\nsee `LICENSE <https://github.com/shollingsworth/jira-freeplane/blob/main/LICENSE.txt>`_\n',
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
