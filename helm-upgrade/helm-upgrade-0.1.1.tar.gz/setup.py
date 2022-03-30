# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['helm_upgrade']

package_data = \
{'': ['*']}

install_requires = \
['bs4==0.0.1',
 'numpy==1.22.3',
 'requests==2.27.1',
 'ruamel.yaml>=0.17.21,<0.18.0']

entry_points = \
{'console_scripts': ['helm-upgrade = helm_upgrade.cli:main']}

setup_kwargs = {
    'name': 'helm-upgrade',
    'version': '0.1.1',
    'description': 'A Python CLI to manage Helm Chart dependencies',
    'long_description': '# helm-upgrade\n\n[![PyPI version](https://badge.fury.io/py/helm-upgrade.svg)](https://badge.fury.io/py/helm-upgrade) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sgibson91/helm-upgrade/main.svg)](https://results.pre-commit.ci/latest/github/sgibson91/helm-upgrade/main) [![CI Tests](https://github.com/sgibson91/helm-upgrade/actions/workflows/ci.yaml/badge.svg)](https://github.com/sgibson91/helm-upgrade/actions/workflows/ci.yaml) [![codecov](https://codecov.io/gh/sgibson91/helm-upgrade/branch/main/graph/badge.svg?token=U2HTE7X6BK)](https://codecov.io/gh/sgibson91/helm-upgrade)\n\nDo you manage a Helm Chart that has dependencies on other Helm Charts?\nAre you fed up of manually updating these dependencies?\nThen this is the tool for you!\n`helm-upgrade` is a Python command line interface (CLI) that automatically updates the dependencies of local Helm Charts.\n\nThis tool was inspired by [`bump-helm-deps-action`](https://github.com/sgibson91/bump-helm-deps-action).\n\n**Table of Contents**\n\n- [:rocket: Installation](#rocket-installation)\n  - [:snake: `pip`](#snake-pip)\n  - [:wrench: Manual](#wrench-manual)\n- [:recycle: Usage](#recycle-usage)\n  - [:wheel_of_dharma: Remote Helm Charts](#wheel_of_dharma-remote-helm-charts)\n- [:white_check_mark: Running Tests](#white_check_mark-running-tests)\n- [:sparkles: Contributing](#sparkles-contributing)\n\n---\n\n## :rocket: Installation\n\nIt\'s recommended to use Python version 3.8 with this tool.\n\n### :snake: `pip`\n\n```bash\npip install helm-upgrade\n```\n\n### :wrench: Manual\n\nFirst of all, clone this repository and change into it.\n\n```bash\ngit clone https://github.com/sgibson91/helm-upgrade.git\ncd helm-upgrade\n```\n\nUse Python to install requirements and the package.\nPython 3.8 is recommended.\n\n```bash\npython -m pip install .\n```\n\nTest the installation by calling the help page.\n\n```bash\nhelm-upgrade --help\n```\n\n## :recycle: Usage\n\n```\nusage: helm-upgrade [-h] [--dry-run] chart_path dependencies\n\nUpdate the dependencies of a local Helm Chart in a project repository.\n\npositional arguments:\n  chart_path    Path to the file containing the dependencies of the local Helm Chart to\n                be updated.\n  dependencies  A dictionary of Helm Chart dependencies and their host repo URLs. E.g.\n                \'{"nginx-ingress":\n                "https://raw.githubusercontent.com/helm/charts/master/stable/nginx-\n                ingress/Chart.yaml"}\'\n\noptional arguments:\n  -h, --help    show this help message and exit\n  --dry-run     Perform a dry run of the update. Don\'t write the changes to a file.\n```\n\n`helm-upgrade` will then:\n\n1) read the current versions of your dependencies from the file you specify,\n2) find the latest versions of your desired dependencies from the URLs provided (in JSON schema) to the `dependencies` argument,\n3) compare whether these versions are equal,\n4) if the versions are not equal (and the `--dry-run` flag has not been set), your helm chart dependencies will be overwritten with the new chart versions.\n\n### :wheel_of_dharma: Remote Helm Charts\n\n`helm-upgrade` currently recognises chart versions from three types of hosts.\n\n1) A `Chart.yaml` file from another GitHub repository.\n   These URLs end with "`/Chart.yaml`".\n\n   For example, [https://raw.githubusercontent.com/helm/charts/master/stable/nginx-ingress/Chart.yaml](https://github.com/helm/charts/blob/master/stable/nginx-ingress/Chart.yaml)\n\n2) A repository of chart versions hosted on GitHub pages.\n   These URLs contain "`/gh-pages/`".\n\n   For example, [https://raw.githubusercontent.com/jupyterhub/helm-chart/gh-pages/index.yaml](https://github.com/jupyterhub/helm-chart/blob/gh-pages/index.yaml)\n\n3) Versions listed on a GitHub Releases page.\n   These URLs end with "`/releases/latest`" and uses `BeautifulSoup` to search the html.\n\n   For example, <https://github.com/jetstack/cert-manager/releases/latest>\n\n## :white_check_mark: Running Tests\n\nTo run the test suite, you must first following the [manual installation instructions](#wrench-manual).\nOnce completed, the test suite can be run as follows:\n\n```bash\npython -m pytest -vvv\n```\n\nTo see code coverage of the test suite, run the following:\n\n```bash\npython -m coverage run -m pytest -vvv\ncoverage report\n```\n\nAn interactive HTML version of the report can be accessed by running the following:\n\n```bash\ncoverage html\n```\n\nAnd then opening the `htmlcov/index.html` file in a browser window.\n\n## :sparkles: Contributing\n\n:tada: Thank you for wanting to contribute! :tada:\nMake sure to read our [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing Guidelines](CONTRIBUTING.md) to get you started.\n',
    'author': 'Sarah Gibson',
    'author_email': 'drsarahlgibson@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
