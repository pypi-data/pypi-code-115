# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['difftree']

package_data = \
{'': ['*']}

entry_points = \
{'console_scripts': ['difftree = difftree.main:entry']}

setup_kwargs = {
    'name': 'difftree',
    'version': '0.1.1',
    'description': 'Diff two directories recursively',
    'long_description': "difftree\n=======\ndifftree is a tool that diffs two directories. It recursively walks through the directories\nand lists files that are missing on either side.\n\nBy default `difftree` only checks whether a file is present or not, so files\npresent on both sides but with different file sizes, permissions or content\nwill not be listed. However, checking any of those can be enabled via\nthe `-s`, `-p`, and `-z` flags respectively.\n\nUsage\n-----\n\n    > difftree dir-a/ dir-b/\n    dir-a/                 <-> dir-b/\n                           <-  file-only-in-dirb.txt\n    file-only-in-dir-a.txt  ->\n\nThe following options are available:\n\n      -h, --help            show this help message and exit\n      -p, --check-perms     Diff file permissions\n      -s, --check-sizes     Diff file sizes\n      -z, --check-hashes    Diff file hashes\n      -d, --dir-norecurse   Show missing directories as a single entry (don't show files in the directory)\n      -e exclude_regex, --exclude exclude_regex\n                            Exclude files matching this regex\n\nInstall\n-------\nThe recommended way to install `difftree` is via [pipx]:\n\n    pipx difftree\n\nAlternatives\n------------\nUNIX built-in `diff -rq dir1 dir2` works quite well.\n\n`rsync --dry-run -r --itemize-changes dir1 dir2` also works quite well, but\ndoesn't list files that are present in `dir2` but missing in `dir1`. It requires you\nto parse the quite terse change format e.g. `>fcsT....` and `>f+++++++`.\n\n\n[pipx]: https://github.com/pypa/pipx",
    'author': 'Malthe Jørgensen',
    'author_email': 'malthe.jorgensen@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/malthejorgensen/difftree',
    'packages': packages,
    'package_data': package_data,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
