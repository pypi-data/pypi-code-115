# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['dollar_lambda']

package_data = \
{'': ['*']}

install_requires = \
['pytypeclass>=0.1.1,<0.2.0']

setup_kwargs = {
    'name': 'dollar-lambda',
    'version': '0.1.7',
    'description': 'An argument parser for Python built from functional first principles',
    'long_description': '# [$λ](https://ethanabrooks.github.io/dollar-lambda/)\n## Not the parser that we need, but the parser we deserve.\n\n`$λ` is an argument parser for python.\nIt was built with minimal dependencies from functional first principles.\nAs a result, it is the most\n\n- versatile\n- type-safe\n- and concise\n\nargument parser on the market.\n\n### Versatile\n`$λ` provides high-level functionality equivalent to other parsers. But unlike other parsers,\nit permits low-level customization to handle arbitrarily complex parsing patterns.\n### Type-safe\n`$λ` uses type annotations as much as Python allows. Types are checked\nusing [`MyPy`](https://mypy.readthedocs.io/en/stable/index.html#) and exported with the package\nso that users can also benefit from the type system.\n### Concise\n`$λ` provides a variety of syntactic sugar options that enable users\nto write parsers with minimal boilerplate.\n\n## [Documentation](https://ethanabrooks.github.io/dollar-lambda/)\n## Installation\n```\npip install -U dollar-lambda\n```\n## Example Usage\nFor simple settings,`@command` can infer the parser for the function signature:\n\n\n```python\nfrom dollar_lambda import command\n\n\n@command()\ndef main(foo: int = 0, bar: str = "hello", baz: bool = False):\n    return dict(foo=foo, bar=bar, baz=baz)\n\n\nmain("-h")\n```\n\n    usage: --foo FOO --bar BAR --baz\n\n\nThis handles defaults:\n\n\n```python\nmain()\n```\n\n\n\n\n    {\'foo\': 0, \'bar\': \'hello\', \'baz\': False}\n\n\n\nAnd of course allows the user to supply arguments:\n\n\n```python\nmain("--foo", "1", "--bar", "goodbye", "--baz")\n```\n\n\n\n\n    {\'foo\': 1, \'bar\': \'goodbye\', \'baz\': True}\n\n\n\n`$λ` can also handle far more complex parsing patterns:\n\n\n```python\nfrom dataclasses import dataclass, field\n\nfrom dollar_lambda import Args, done\n\n\n@dataclass\nclass Args1(Args):\n    many: int\n    args: list = field(default_factory=list)\n\n\nfrom dollar_lambda import field\n\n\n@dataclass\nclass Args2(Args):\n    different: bool\n    args: set = field(type=lambda s: {int(x) for x in s}, help="this is a set!")\n\n\np = (Args1.parser() | Args2.parser()) >> done()\n```\n\nYou can run this parser with one set of args:\n\n\n```python\np.parse_args("--many", "2", "--args", "abc")\n```\n\n\n\n\n    {\'many\': 2, \'args\': [\'a\', \'b\', \'c\']}\n\n\n\nOr the other set of args:\n\n\n```python\np.parse_args("--args", "123", "--different")  # order doesn\'t matter\n```\n\n\n\n\n    {\'args\': {1, 2, 3}, \'different\': True}\n\n\n\nBut not both:\n\n\n```python\np.parse_args("--many", "2", "--different", "--args", "abc")\n```\n\n    usage: [--many MANY --args ARGS | --different --args ARGS]\n    args: this is a set!\n    Expected \'--args\'. Got \'--different\'\n\n\n### Thanks\nSpecial thanks to ["Functional Pearls"](https://www.cs.nott.ac.uk/~pszgmh/pearl.pdf) by Graham Hutton and Erik Meijer for bringing these topics to life.\n',
    'author': 'Ethan Brooks',
    'author_email': 'ethanabrooks@gmail.com',
    'maintainer': 'Ethan Brooks',
    'maintainer_email': 'ethanabrooks@gmail.com',
    'url': 'https://ethanabrooks.github.io/dollar-lambda/',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
