# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['ireval']

package_data = \
{'': ['*']}

install_requires = \
['numpy>=1.22.3,<2.0.0']

setup_kwargs = {
    'name': 'ireval',
    'version': '0.1.0',
    'description': '',
    'long_description': '# ireval\n\nThis Python package provides an implementation of the most common information retrieval (IR) metrics.\nOur goal is to return the same scores as [trec_eval](https://github.com/usnistgov/trec_eval).\nWe achieve this by extensively comparing our implementations across many different datasets with their results.\n`ireval` can be installed via\n\n    pip install ireval\n\n## Implemented metrics\n\nThe following metrics are currently implemented:\n\n| Name              | Function                 | Description                                                                                                                                              |\n|-------------------|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|\n| Precision@k       | `precision_at_k`         | Precision is the fraction of retrieved documents that are relevant to the query. Precision@k considers only the documents with the highest `k` scores.   |\n| Precision@k%      | `precision_at_k_percent` | Precision is the fraction of retrieved documents that are relevant to the query. Precision@k% considers only the documents with the highest `k`% scores. |\n| Recall@k          | `recall_at_k`            | Recall is the fraction of the relevant documents that are successfully retrieved. Recall@k considers only the documents with the highest `k` scores.     |\n| Recall@k%         | `recall_at_k_percent`    | Recall is the fraction of the relevant documents that are successfully retrieved. Recall@k% considers only the documents with the highest `k`% scores.   |\n| Average precision | `average_precision`      | Average precision is the area under the precision-recall curve.                                                                                          |\n| R-precision       | `r_precision`            | R-Precision is the precision after R documents have been retrieved, where R is the number of relevant documents for the topic.                           | |\n\n## Usage\n\n```python\nimport ireval\n\nrelevancies = [1, 0, 1, 1, 0]\nscores = [0.1, 0.4, 0.35, 0.8]\n\np5 = ireval.precision_at_k(relevancies, scores, 5)\np5pct = ireval.precision_at_k_percent(relevancies, scores, 5)\n\nr5 = ireval.recall_at_k(relevancies, scores, 5)\nr5pct = ireval.recall_at_k_percent(relevancies, scores, 5)\n\nap = ireval.average_precision(relevancies, scores)\nrprec = ireval.r_precision(relevancies, scores)\n```\n',
    'author': 'Jan-Christoph Klie ',
    'author_email': 'git@mrklie.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/jcklie/ireval',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
