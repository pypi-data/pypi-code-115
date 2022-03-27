# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['pytest_base_url']

package_data = \
{'': ['*']}

install_requires = \
['pytest>=3.0.0,<8.0.0', 'requests>=2.9']

entry_points = \
{'pytest11': ['base_url = pytest_base_url.plugin']}

setup_kwargs = {
    'name': 'pytest-base-url',
    'version': '2.0.0',
    'description': 'pytest plugin for URL based testing',
    'long_description': 'pytest-base-url\n===============\n\npytest-base-url is a simple plugin for pytest_ that provides an optional base\nURL via the command line or configuration file.\n\n.. image:: https://img.shields.io/badge/license-MPL%202.0-blue.svg\n   :target: https://github.com/pytest-dev/pytest-base-url/blob/master/LICENSE\n   :alt: License\n.. image:: https://img.shields.io/pypi/v/pytest-base-url.svg\n   :target: https://pypi.python.org/pypi/pytest-base-url/\n   :alt: PyPI\n.. image:: https://img.shields.io/travis/pytest-dev/pytest-base-url.svg\n   :target: https://travis-ci.org/pytest-dev/pytest-base-url/\n   :alt: Travis\n.. image:: https://img.shields.io/github/issues-raw/pytest-dev/pytest-base-url.svg\n   :target: https://github.com/pytest-dev/pytest-base-url/issues\n   :alt: Issues\n.. image:: https://img.shields.io/requires/github/pytest-dev/pytest-base-url.svg\n   :target: https://requires.io/github/pytest-dev/pytest-base-url/requirements/?branch=master\n   :alt: Requirements\n\nRequirements\n------------\n\nYou will need the following prerequisites in order to use pytest-base-url:\n\n- Python 3.7+ or PyPy3\n\nInstallation\n------------\n\nTo install pytest-base-url:\n\n.. code-block:: bash\n\n  $ pip install pytest-base-url\n\nContributing\n------------\n\nWe welcome contributions.\n\nTo learn more, see `Development <https://github.com/pytest-dev/pytest-base-url/blob/master/development.rst>`_\n\nSpecifying a Base URL\n---------------------\n\nRather than repeating or abstracting a base URL in your tests, pytest-base-url\nprovides a ``base_url`` fixture that returns the specified base URL.\n\n.. code-block:: python\n\n  import urllib2\n\n  def test_example(base_url):\n      assert 200 == urllib2.urlopen(base_url).getcode()\n\nUsing the Command Line\n^^^^^^^^^^^^^^^^^^^^^^\n\nYou can specify the base URL on the command line:\n\n.. code-block:: bash\n\n  $ py.test --base-url http://www.example.com\n\nUsing a Configuration File\n^^^^^^^^^^^^^^^^^^^^^^^^^^\n\nYou can specify the base URL using a `configuration file`_:\n\n.. code-block:: ini\n\n  [pytest]\n  base_url = http://www.example.com\n\nUsing an Environment Variable\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\nYou can specify the base URL by setting the ``PYTEST_BASE_URL`` environment variable.\n\nUsing a Fixture\n^^^^^^^^^^^^^^^\n\nIf your test harness takes care of launching an instance of your application\nunder test, you may not have a predictable base URL to provide on the command\nline. Fortunately, it\'s easy to override the ``base_url`` fixture and return\nthe correct URL to your test.\n\nIn the following example a ``live_server`` fixture is used to start the\napplication and ``live_server.url`` returns the base URL of the site.\n\n.. code-block:: python\n\n  import urllib2\n  import pytest\n\n  @pytest.fixture\n  def base_url(live_server):\n      return live_server.url\n\n  def test_search(base_url):\n      assert 200 == urllib2.urlopen(\'{0}/search\'.format(base_url)).getcode()\n\nAvailable Live Servers\n----------------------\n\nIt\'s relatively simple to create your own ``live_server`` fixture, however you\nmay be able to take advantage of one of the following:\n\n* Django applications can use pytest-django_\'s  ``live_server`` fixture.\n* Flask applications can use pytest-flask_\'s ``live_server`` fixture.\n\nVerifying the Base URL\n----------------------\n\nIf you specify a base URL for a site that\'s unavailable then all tests using\nthat base URL will likely fail. To avoid running every test in this instance,\nyou can enable base URL verification. This will check the base URL is\nresponding before proceeding with the test suite. To enable this, specify the\n``--verify-base-url`` command line option or set the ``VERIFY_BASE_URL``\nenvironment variable to ``TRUE``.\n\nSkipping Base URLs\n------------------\n\nYou can `skip tests`_ based on the value of the base URL so long as it is\nprovided either by the command line or in a configuration file:\n\n.. code-block:: python\n\n  import urllib2\n  import pytest\n\n  @pytest.mark.skipif(\n      "\'dev\' in config.getoption(\'base_url\')",\n      reason=\'Search not available on dev\')\n  def test_search(base_url):\n      assert 200 == urllib2.urlopen(\'{0}/search\'.format(base_url)).getcode()\n\nUnfortunately if the URL is provided by a fixture, there is no way to know this\nvalue at test collection.\n\nResources\n---------\n\n- `Release Notes`_\n- `Issue Tracker`_\n- Code_\n\n.. _pytest: http://www.python.org/\n.. _configuration file: http://pytest.org/latest/customize.html#command-line-options-and-configuration-file-settings\n.. _pytest-django: http://pytest-django.readthedocs.org/\n.. _pytest-flask: http://pytest-flask.readthedocs.org/\n.. _skip tests: http://pytest.org/latest/skipping.html\n.. _Release Notes:  http://github.com/pytest-dev/pytest-base-url/blob/master/CHANGES.rst\n.. _Issue Tracker: http://github.com/pytest-dev/pytest-base-url/issues\n.. _Code: http://github.com/pytest-dev/pytest-base-url\n',
    'author': 'Dave Hunt',
    'author_email': 'dhunt@mozilla.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/pytest-dev/pytest-base-url',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
