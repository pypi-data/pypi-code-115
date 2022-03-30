import setuptools
from pathlib import Path

setuptools.setup(
    name='Dym_Env',
    version='0.0.1',
    description='A OpenAI Gym Env for Dym',
    long_description=Path('README.md').read_text(),
    packages=setuptools.find_packages(include='Dym_Env*'),
    requires=['gym'],
)