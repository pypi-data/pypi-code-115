from setuptools import setup, find_packages
import os


VERSION = '0.0.2'
DESCRIPTION = 'Tissue Image Analysis'
LONG_DESCRIPTION = 'A package that perform integrated analysis of cells and ECM fibers in a spatially dependent manner.'

# Setting up
setup(
    name="microsaa",
    version=VERSION,
    author="Georgii Vasiukov",
    author_email="<vasyukov.georgiy.yu@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION ,
    packages=find_packages(),
    install_requires=['scikit-image','numpy','matplotlib','scipy','pandas'],
    keywords=['python', 'spatial', 'collagen', 'cells ', 'integrated'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
