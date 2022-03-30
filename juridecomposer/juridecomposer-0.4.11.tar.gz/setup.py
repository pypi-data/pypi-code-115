# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['juridecomposer']

package_data = \
{'': ['*']}

install_requires = \
['pandas>=1.0.5,<2.0.0', 'xmltodict>=0.12.0,<0.13.0']

entry_points = \
{'console_scripts': ['my-script = '
                     'src.juridecomposer.juridecomposer:xml_to_dataframe']}

setup_kwargs = {
    'name': 'juridecomposer',
    'version': '0.4.11',
    'description': '',
    'long_description': '# Juridecomposer\n\nThe Juridecomposer package can be used to transform Dutch laws structured as .xml files into pandas dataframes. \nInput laws can be retrieved from [wetten.nl](https://wetten.overheid.nl/). \n\n# Example usage\n\n    from juridecomposer.juridecomposer import xml_to_dataframe\n    output_dataframe = xml_to_dataframe("path/to/law/xml")\n\nThe output dataframe will consist of the following columns:\n- Brontekst: raw extracted text;\n- Nummer: specifies the chapter (hoofdstuk) number;\n- Lid: specificies the section (afdeling) number;\n- Opsomming niveau 1: specifies the article (artikel) number;\n- Opsomming niveau 2: specifies the component (onderdeel) number;\n- Opsomming niveau 3: specifies the second component (onderdeel) number, if available; \n- Versie: specifies the version number;\n- jc 1.3: permanent link to specific section.\n\n\n\n',
    'author': 'Roos Bakker',
    'author_email': 'roos.bakker@tno.nl',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://gitlab.com/calculemus-flint/flintfillers/flintfiller-rlb',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.6.1,<3.7',
}


setup(**setup_kwargs)
