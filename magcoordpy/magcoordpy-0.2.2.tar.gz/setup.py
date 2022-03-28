# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['magcoordpy']

package_data = \
{'': ['*'], 'magcoordpy': ['data/*']}

install_requires = \
['numpy>=1.22.2,<2.0.0', 'pymap3d>=2.7.2,<3.0.0', 'urllib3>=1.26.8,<2.0.0']

setup_kwargs = {
    'name': 'magcoordpy',
    'version': '0.2.2',
    'description': 'A python package for working with magnetic coordinate transformations',
    'long_description': '# MagCoordPy\n\n![test-main](https://github.com/giorgiosavastano/magcoordpy/actions/workflows/python-test-main.yml/badge.svg)\n![coverage-main](https://img.shields.io/codecov/c/github/giorgiosavastano/magcoordpy)\n![license](https://img.shields.io/github/license/giorgiosavastano/magcoordpy)\n\nA python package for working with magnetic coordinate transformations.\nThe documentation is available at <https://magcoordpy.readthedocs.io/en/latest/>.\n\nInstallation\n------------\n\n    pip install magcoordpy\n\nExample usage\n-------------\n\n    from magcoordpy import coord_transforms\n    long_geo = np.arange(-180, 190, 10)\n    lati_geo = np.zeros(len(long_array))\n    alti_geo = np.zeros(len(long_array))\n    lat_cd, lon_cd, r_cd = coord_transforms.geodetic2cd(lati_geo, long_geo, alti_geo, year=2021.0)\n\n\nIt includes the following functions (not exhaustive list):\n\n* geodetic2cd --> transformation from geodetic to centered dipole\n* cd2geodetic --> transformation from centered dipole to geodetic\n\n\n## Authors\n\n- Giorgio Savastano (<giorgiosavastano@gmail.com>)\n\nPlease use github issues to make bug reports and request new functionality. Contributions are always welcome.\n\n## References\n\nLaundal, K.M., Richmond, A.D. Magnetic Coordinate Systems. Space Sci Rev 206, 27–59 (2017). <https://doi.org/10.1007/s11214-016-0275-y>\n',
    'author': 'Giorgio Savastano',
    'author_email': 'giorgio.savastano@uniroma1.it',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
