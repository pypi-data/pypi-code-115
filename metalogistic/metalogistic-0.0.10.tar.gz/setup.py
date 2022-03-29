# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['metalogistic']

package_data = \
{'': ['*']}

install_requires = \
['matplotlib>=3.5.1,<4.0.0', 'numpy>=1.22.3,<2.0.0', 'scipy>=1.8.0,<2.0.0']

setup_kwargs = {
    'name': 'metalogistic',
    'version': '0.0.10',
    'description': 'A Python package for the metalogistic distribution. The metalogistic or metalog distribution is a highly flexible probability distribution that can be used to model data without traditional parameters.',
    'long_description': '# The metalog distribution\nThis package is a Python implementation of the **metalogistic or metalog** distribution,\nas described in [Keelin 2016][k2016].\n\nThe metalog is a continuous univariate probability distribution that can be used to model data without traditional parameters.\nInstead, the distribution is parametrized by **points on a cumulative distribution function (CDF)**, and the CDF of the\nmetalog fitted to these input points usually passes through them exactly.\nThe distribution can take almost any shape.\n\nThe distribution is well suited to **eliciting full subjective probability distributions** from a few\n CDF points. If used in this way, the result is a distribution that fits these points closely, without\n imposing strong shape constraints (as would be the case if fitting to a traditional distribution like the \n normal or lognormal). [Keelin 2016][k2016] remarks that the metalog "can be used for real-time feedback to experts\n about the implications of their probability assessments".\n\nSee also the website [metalogdistributions.com](http://www.metalogdistributions.com/).\n\n[k2016]: http://www.metalogdistributions.com/images/The_Metalog_Distributions_-_Keelin_2016.pdf\n\n# This package\nThis package:\n* Provides an object-oriented interface to instances of the class `MetaLogistic`\n* Defines `MetaLogistic` as a subclass of SciPy [continuous distribution objects](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.rv_continuous.html),\nwhich lets us use their many convenient, performant methods.\n* Uses numerical methods to approximate a least-squares fit if the closed-form method described in Keelin 2016 fails.\n This allows us to fit an even wider range of CDF data. \n* Is fast (see `timings.py`).\n \n\n# Usage\n\n```python\nfrom metalogistic import MetaLogistic\n\nmy_metalog = MetaLogistic(cdf_xs=[-5, 2, 20], cdf_ps=[.35, .5, .95])\n\n# These methods can take scalars or arrays/lists/vectors\nmy_metalog.cdf(10)\nmy_metalog.pdf([10, 20, 21])\nmy_metalog.quantile([0.8, .99])\n\n# These methods conveniently display useful information\nmy_metalog.print_summary()\nmy_metalog.display_plot()\n```\n\nSee also `example_usage.py`\n\n# Installation \n```\npip install metalogistic\n```\n\n# Speed\n`timings.py`\n\nWhen using linear least squares:\n```\n#### Speed test ####\nData:\ncdf_ps [0.15, 0.5, 0.9]\ncdf_xs [-20, -1, 40]\nBounds: None None\n\nTimings:\n\'doFit\'  3.99 ms\n\'createPlotData\'  3.99 ms\n```\n\nWhen we are forced to use numerical fitting methods:\n```\n#### Speed test ####\nData:\ncdf_ps [0.15, 0.5, 0.9]\ncdf_xs [-20, -1, 100]\nBounds: None 1000\n\nTimings:\n\'doFit\'  345.08 ms\n\'createPlotData\'  4.98 ms\n\n#### Speed test ####\nData:\ncdf_ps [0.15, 0.5, 0.9]\ncdf_xs [-20, -1, 100]\nBounds: None None\n\nTimings:\n\'doFit\'  354.57 ms\n\'createPlotData\'  5.98 ms\n```\n\n# License\nIf AGPL is a problem for you, please [contact me](https://tadamcz.com/). As I am currently the sole author, we can probably work something out.\n',
    'author': 'tadamcz',
    'author_email': 'tmkadamcz@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/tadamcz/metalogistic',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<3.9',
}


setup(**setup_kwargs)
