# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['build_fingerprinter']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=6.0,<7.0', 'pydantic>=1.9.0,<2.0.0']

entry_points = \
{'console_scripts': ['fingerprinter = build_fingerprinter.cli:main']}

setup_kwargs = {
    'name': 'uw-it-build-fingerprinter',
    'version': '0.1.1',
    'description': 'A library and CLI to aid in configuring layered fingerprints.',
    'long_description': "# Fingerprinter\n\nThis utility library can be used to create SHA256 fingerprints\nusing globs and paths. It is meant to be a replacement\nfor the `sources/fingerprints.sh` in \n[common-build-scripts].\n\n## Installation\n\n```\npip install uw-it-build-fingerprinter\n```\n\n## Use\n\n```\nfingerprinter --help\nfingerprinter -f fingerprints.yml -t assets\n```\n\n\n### Configuration File\n\nTo get started, you'll need a configuration file. This file is a yaml file\nthat defines your fingerprint targets. \n\n```yaml\ntargets:\n  target-name: \n    include-paths:\n      - src/**/*.py   # Glob to match all python files recursively under a directory\n      - src/        # Will match every file under src/, recursively. (Same as 'src/**/*.*)\n      - src         # interchangeable with `src/` or `src/**/*.*`\n      - src/foo.py  # Include a specific file\n```\n\nYou may also declare other targets as dependencies:\n\n```yaml\n# This example has a source fingerprint that is generated for all python files\n# under the src/ directory, but the fingerprint is dependent on the \n# dependency locks. This means that even if all python files remain\n# untouched, an update to the dependencies will generate a new\n# source fingerprint. \n# `fingerprints.yaml` is also included here to ensure that changes\n# to the actual fingerprint configuration regenerates all fingerprints.\ntargets:\n  dependencies:\n    include-paths:\n      - poetry.lock\n      - fingerprints.yaml \n  source:\n    depends-on: [dependencies]\n    include-paths: ['src/**/*.py']\n```\n\n**All paths will be lexicographically sorted at runtime**, however dependencies\nare always resolved in the order provided.\n\n`python -m fingerprinter.cli -f fingerprints.yaml -t source` will do the rest!\n\n### Excluding Files\n\nThere may be some paths that you never want to consider. \n`.pyc`, `__pycache__` and `.pytest_cache/` are always ignored by default.\n\nYou can exclude paths at the base of your yaml:\n\n```yaml\nignore-paths:\n  - '**/ignore-me.py'  # Ignore every 'ignore-me.py' in the tree\n  - 'src/special/ignore-me-also.py'  # Ignores this specific file \n\ntargets:\n  foo:\n    # Will include src/foo/bar, but not src/.secrets/sekret or src/foo/__pycache__/blah\n    include-paths: ['src']\n```\n\n[common-build-scripts]: https://github.com/uwit-iam/common-build-scripts\n",
    'author': 'Tom Thorogood',
    'author_email': 'goodtom@uw.edu',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/uwit-iam/build-fingerprinter',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8',
}


setup(**setup_kwargs)
