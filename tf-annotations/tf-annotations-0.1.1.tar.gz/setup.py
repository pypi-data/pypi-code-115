# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['tf_annotations']

package_data = \
{'': ['*']}

install_requires = \
['toml>=0.10.2,<0.11.0']

entry_points = \
{'console_scripts': ['tf-annotations = tf_annotations.cmd:cli']}

setup_kwargs = {
    'name': 'tf-annotations',
    'version': '0.1.1',
    'description': 'Tool to report on annotations such as TODO',
    'long_description': '# code-annotations\n\nThis project was created as a way of creating a central "annotation" file of all the useful\nnotes that might be created in a code base such as `TODO` comments.\n\n## Configuration\n\nThe project can be configured via a TOML file which by default is called `.tf-annotations.toml` but can be override with the `--config` flag.\n\nBelow is an example which can be found at `.tf-annotations-example.toml`\n\n```TOML\ntitle = "Code Annotation Config file"\n\nfile_suffix=["*.tf"]\nheaders=["TODO","KNOWISSUES"]\noutput_file="ANNOTATIONS.md"\ncomment_syntax = ["#", "//"]\n```\n',
    'author': 'Russell Whelan',
    'author_email': 'russell.whelan+python@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
