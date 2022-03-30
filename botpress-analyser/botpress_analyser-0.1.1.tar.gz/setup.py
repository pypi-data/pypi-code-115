# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['nlp_analyser']

package_data = \
{'': ['*']}

install_requires = \
['LanguageIdentifier>=1.1.1,<2.0.0',
 'bertopic>=0.9.4,<0.10.0',
 'click==8.0.4',
 'pandas-profiling>=3.1.0,<4.0.0',
 'rich>=11.1.0,<12.0.0',
 'spacy>=3.2.1,<4.0.0',
 'streamlit>=1.8.0,<2.0.0']

entry_points = \
{'console_scripts': ['nlp_analyser = nlp_analyser.cli:cli']}

setup_kwargs = {
    'name': 'botpress-analyser',
    'version': '0.1.1',
    'description': 'A package to make clusters from a corpus',
    'long_description': "# NLP Analyser tool\n\nThis tool provide a small GUI to cluster a corpus\n\nFor now it support only csv files and txt files.\n\n# Using the GUI\n\nWe provide a small gui to help less technical users.\n## Launching the gui\nOnce installed, run `nlp_analyser gui` to launch the app. \n\nIt will launch on localhost, port 8501 by default.\n\nYou can then go to http://localhost:8501 and use the tool.\n\n## Using a csv file\nWe provide a small utility to convert a csv file to a txt one. \n\nYou __need__ to provide the column index where the text is and the csv delimiter.\n\nBy default it's `0` and `,` \n\nThen you can import any csv file, right after importing, a button will appear in the sidebar and you will be able to download the converted txt file.\n\nThen the tool will automatically use this new converted text file as if you exported that in the first time.\n## Using a txt file\n\nYou have nothing to do when using a text file. \nJust ensure that it's one sentence per line.\n\nButtons will appear and you will be able to analyse and cluster your corpus\n\n# Analysis\nWhen analyzing the corpus, we provide a progress bar. However, the operation might be really slow on big corpuses....\n\nWhen clustering, we have no way to report progress but that can also be long for huge files...\n\n\n# Using the cli \n\nWe also provide a cli for users that prefer to use the command line.\n\nAfter installing you can access it with `nlp_analyser --help` and follow from there.\n\nIt provide the same command as the gui : converting a csv and analyzing the corpus.",
    'author': 'Pierre Snell',
    'author_email': 'pierre.snell@botpress.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
