# -*- coding: utf-8 -*-
from setuptools import setup

modules = \
['immute']
setup_kwargs = {
    'name': 'immute',
    'version': '0.2.1',
    'description': 'Create immutable python classes',
    'long_description': '# Immute\n\nCreate "immutable" classes in python.\n\nI created a simple python object that, when inherited in another class, will prevent assignment operations outside the `\\_\\_init__()` method.\n\n**Note: DOES NOT CREATE TRUELY IMMUTABLE REFERENCES**\n\nClasses inheriting from `Immutable` are not immutable references, only immutable from assignments, reassignment and deletion operations.\n\nClasses inheriting from `Immutable` are still mutable reference types, and not truly immutable like python\'s built-in types (int, float, bool, str, tuples).\n\n## Example\n\n```python\nfrom immute import Immutable\n\nclass Thing(Immutable):\n    def __init__(self) -> None:\n        self.num = 42\n\nthing = Thing()\n\nthing.num = 21\n# ^^^^^^ This will raise a TypeError exception\n```\n',
    'author': 'fitzypop',
    'author_email': 'fitzypop@pm.me',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/fitzypop/immute',
    'py_modules': modules,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
