"""Module for package setup."""
from setuptools import find_packages, setup

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='dxi_nlp',
    url='https://github.com/Edelman-DxI/dxi-nlp.git',
    author='Amit Prusty',
    author_email='amit.prusty@edelmandxi.com',
    # Needed to actually package something
    packages=find_packages(),
    namespace_packages=['dxi_nlp'],
    # Needed for dependencies
    install_requires=[
        'numpy', 'logging', 'pandas', 'spacy',
        'boto3', 's3fs', 'matplotlib', 'tqdm',
        'pyarrow', 'labelbox',
    ],
    # *strongly* suggested for in-house use
    version='0.1',
    # The license can be anything you like
    license='Private',
    description='',
    # We will also need a readme eventually (there will be a warning)
    long_description=open('README.md').read(),
)
