from setuptools import find_packages, setup

setup(
    name="ltbfiles",
    author="Sven Merk",
    description="Module for loading of files created with spectrometers from LTB",
    packages=find_packages(),
    include_package_data=True,
    url="https://gitlab.com/ltb_berlin/ltb_files",
    install_requires=['numpy'],
    extras_require={
        'tests': ['pytest'],
        'publish': ['twine'],
    }
)