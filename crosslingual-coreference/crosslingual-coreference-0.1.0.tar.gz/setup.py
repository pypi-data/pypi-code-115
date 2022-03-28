# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['crosslingual_coreference', 'crosslingual_coreference.examples']

package_data = \
{'': ['*']}

install_requires = \
['allennlp-models>=2.9.0,<3.0.0',
 'allennlp>=2.9.2,<3.0.0',
 'spacy>=3.0.0,<4.0.0']

setup_kwargs = {
    'name': 'crosslingual-coreference',
    'version': '0.1.0',
    'description': 'A multi-lingual approach to AllenNLP CoReference Resolution, along with a wrapper for spaCy.',
    'long_description': '# crosslingual-coreference\nCoreference is amazing but the data required for training a model is very scarce. In our case, the available training for non-English languages also data proved to be poorly annotated. Crosslingual Coreference therefore uses the assumption a trained model with English data and cross-lingual embeddings should work for languages with similar sentence structure. \n\n# Install\n\n```\npip install crosslingual-coreference\n```\n# Quickstart\n```python\nfrom crosslingual_coreference import Predictor\n\ntext = "Do not forget about Momofuku Ando! He created instant noodles in Osaka. At that location, Nissin was founded. Many students survived by eating these noodles, but they don\'t even know him."\n\npredictor = Predictor(language="en_core_web_sm", device=-1, model="info_xlm")\n\nprint(predictor.predict(text)["resolved_text"])\n# Output\n# \n# Do not forget about Momofuku Ando! \n# Momofuku Ando created instant noodles in Osaka. \n# At Osaka, Nissin was founded. \n# Many students survived by eating instant noodles, \n# but Many students don\'t even know Momofuku Ando.\n```\n![](https://raw.githubusercontent.com/Pandora-Intelligence/crosslingual-coreference/master/img/example_en.png)\n## Use spaCy pipeline\n```python\nimport crosslingual_coreference\nimport spacy\n\ntext = "Do not forget about Momofuku Ando! He created instant noodles in Osaka. At that location, Nissin was founded. Many students survived by eating these noodles, but they don\'t even know him."\n\nnlp = spacy.load(\'en_core_web_sm\')\nnlp.add_pipe(\'xx_coref\')\n\ndoc = nlp(text)\nprint(doc._.coref_clusters)\n# Output\n# \n# [[[4, 5], [7, 7], [27, 27], [36, 36]], \n# [[12, 12], [15, 16]], \n# [[9, 10], [27, 28]], \n# [[22, 23], [31, 31]]]\nprint(doc._.resolved_text)\n# Output\n# \n# Do not forget about Momofuku Ando! \n# Momofuku Ando created instant noodles in Osaka. \n# At Osaka, Nissin was founded. \n# Many students survived by eating instant noodles, \n# but Many students don\'t even know Momofuku Ando.\n```\n## Available models\nAs of now, there are two models available "info_xlm", "xlm_roberta", which scored 77 and 74 on OntoNotes Release 5.0 English data, respectively.\n## More Examples\n![](https://raw.githubusercontent.com/Pandora-Intelligence/crosslingual-coreference/master/img/example_total.png)\n\n',
    'author': 'David Berenstein',
    'author_email': 'david.berenstein@pandoraintelligence.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/pandora-intelligence/crosslingual-coreference',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7.1,<4.0',
}


setup(**setup_kwargs)
