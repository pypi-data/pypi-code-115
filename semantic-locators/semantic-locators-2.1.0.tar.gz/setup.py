# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

modules = \
['semantic_locators']
install_requires = \
['importlib-resources>=5.1.2,<6.0.0', 'selenium>=3.141.0,<4.0.0']

setup_kwargs = {
    'name': 'semantic-locators',
    'version': '2.1.0',
    'description': 'Semantic Locators are a human readable, resilient and accessibility-enforcing way to find web elements. This package adds semantic locator support to webdriver',
    'long_description': '# Semantic Locators in Python WebDriver\n\nSemantic locators can be used with Selenium WebDriver in a similar way to\n`ByXPath` or `ByCssSelector`. Currently only available for Python 3.6+.\n\nInstall from PyPi:\n\n`python -m pip install semantic-locators`\n\nOnce installed, use Semantic Locators as follows:\n\n```python\nfrom semantic_locators import (\n    find_element_by_semantic_locator,\n    find_elements_by_semantic_locator,\n    closest_precise_locator_for,\n)\n...\n\nsearch_button = find_element_by_semantic_locator(driver, "{button \'Google search\'}")\nall_buttons = find_elements_by_semantic_locator(driver, "{button}")\n\ngenerated = closest_precise_locator_for(search_button); # {button \'Google search\'}\n```\n\nGeneral Semantic Locator documentation can be found on\n[GitHub](http://github.com/google/semantic-locators#readme).\n',
    'author': 'Alex Lloyd',
    'author_email': 'alexlloyd@google.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/google/semantic-locators',
    'package_dir': package_dir,
    'py_modules': modules,
    'install_requires': install_requires,
    'python_requires': '>=3.6,<3.10',
}


setup(**setup_kwargs)
