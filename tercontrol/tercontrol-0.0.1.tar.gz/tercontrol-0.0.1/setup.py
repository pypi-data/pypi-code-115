from setuptools import find_packages
from distutils.core import setup
from Cython.Build import cythonize
import numpy as np

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    # Build both
    #ext_modules=cythonize(["tercontrol.pyx", "terminfo.pyx"]),
    
    # Build `tercontrol.pyx`
    #ext_modules=cythonize("tercontrol.pyx"),
 
    # Build `terminfo.pyx`
    #ext_modules=cythonize("terminfo.pyx"),
    name="tercontrol",
    version="0.0.1",
    packages=find_packages(),
    author="Zackery .R. Smith",
    description="Currently testing the PYPI package. Description will be updated later!",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/ZackeryRSmith/tercontrol",
    ext_modules=cythonize(["tercontrol/tercontrol.pyx", "tercontrol/libs/terminfo.pyx"]),
    include_dirs=np.get_include(),
    install_requires=[
        #'numpy>=1.19.2',
        'PyGObject;platform_system=="Linux"',
    ]
)
