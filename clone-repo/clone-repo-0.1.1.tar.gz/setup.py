# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['clone_repo']

package_data = \
{'': ['*']}

install_requires = \
['click<8.1.0', 'rich>=12.0,<13.0', 'structlog>=21.5,<22.0', 'typer>=0.4,<0.5']

entry_points = \
{'console_scripts': ['clone-repo = clone_repo.main:app']}

setup_kwargs = {
    'name': 'clone-repo',
    'version': '0.1.1',
    'description': 'CLI tool to clone repos easily',
    'long_description': "# clone-repo: Easily clone repos\n\n- [Home](https://github.com/micktwomey/clone-repo)\n- [PyPI](https://pypi.org/project/clone-repo/)\n\n## What is this?\n\nFor years I've been using a noddy script which clones many types of repos into a fixed location which is generated based on the repo itself. Similar to how go packages are cloned into go/src I typically clone my stuff into ~/src.\n\ne.g. `clone-repo git@github.com:micktwomey/clone-repo.git` will clone using git to `~/src/github.com/micktwomey/clone-repo`.\n\nThis allows me to clone many different repos without worrying about stepping on each other. It also makes it easy to see where stuff comes from (e.g. `rm -rf ~/src/old.git.example.com` will wipe out clones from git server I don't use any more).\n\nInstall via `pip install clone-repo`.\n\nInstall with [pipx](https://pypa.github.io/pipx/) using `pipx install clone-repo` to make it available as a CLI tool everywhere.\n\nSupports:\n\n- `/path/to/repo`\n  - `git clone` to `~/src/localhost/file/{repo}`\n- `file:///path/to/repo`\n  - `git clone` to `~/src/localhost/file/{repo}`\n- `git@example.com:org/repo.git`\n  - `git clone` to `~/src/{host}/{org}/{repo}`\n- `https://github.com/org/repo.git`\n  - `git clone` to `~/src/github.com/{org}/{repo}`\n- `https://gitlab.example.com/org/repo.git`\n  - `git clone` to `~/src/{host}/{org}/{repo}`\n- `https://hg.mozilla.org/mozilla-central/`\n  - `hg clone` to `~/src/hg.mozilla.org/{org}/{repo}`\n- `https://hg.sr.ht/~org/repo`\n  - `hg clone` to `~/src/hg.sr.ht/{org}/{repo}`\n- `keybase://team/org/repo`\n  - `git clone` to `~/src/keybase/{org}/{repo}`\n- `man@man.sr.ht:~org/repo`\n  - `git clone` to `~/src/man.sr.ht/{org}/{repo}`\n- `ssh://git@example.com:7999/somegroup/myrepo.git`\n  - `git clone` to `~/src/{host}/{org}/{repo}`\n- `ssh://hg@bitbucket.org/org/repo`\n  - `hg clone` to `~/src/{host}/{org}/{repo}`\n\nFor `https://` URLs the default is git but some will behave differently based on the domain.\n\n# Development\n\nIf you want to quickly develop you can use [poetry](https://python-poetry.org) and [pytest](https://pytest.org/):\n\n1. `poetry install`\n2. `pytest -vv`\n\nIf you want to test across all supported Python versions you can install them via [asdf](https://asdf-vm.com) and then use [nox](https://nox.thea.codes):\n\n1. `asdf install`\n2. `poetry install`\n3. `nox`\n\nIf you want to run [pre-commit](https://pre-commit.com) hooks before committing:\n\n1. `poetry install`\n2. `pre-commit install`\n\nFinally, there is a [just](https://github.com/casey/just) justfile to run some commands.\n",
    'author': 'Michael Twomey',
    'author_email': 'mick@twomeylee.name',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/micktwomey/clone-repo',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
