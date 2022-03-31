from setuptools import find_packages, setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='SE_social',
    packages=find_packages(include=['sesocial']),
    version='1.2.3',
    description='A python library for verifying and generating swedish social security numbers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='WaldemarBjornstrom',
    author_email='Waldemar.bjornstrom@unfnorrbotten.se',
    url='https://github.com/WaldemarBjornstrom/SEsocial',
    license='MIT',
    classifiers=[
    'License :: OSI Approved :: MIT License',
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 5 - Production/Stable',

    'Intended Audience :: Developers',

    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
],
)
