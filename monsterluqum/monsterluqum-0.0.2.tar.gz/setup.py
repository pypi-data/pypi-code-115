# -*- coding: utf-8 -*-
from setuptools import setup

from luqum import __version__


with open('README.rst', 'r') as f:
    long_description = f.read()
with open('CHANGELOG.rst', 'r') as f:
    long_description += "\n\n" + f.read()


setup(
    name='monsterluqum',
    version="0.0.2",
    description="A Lucene query parser generating ElasticSearch queries and more !",
    long_description=long_description,
    author='Kshitij',
    author_email='kshitij.solr@gmail.com',
    url='https://github.com/kshitij91/luqum',
    packages=[
        'luqum',
        'luqum.elasticsearch'
    ],
    install_requires=[
        'ply>=3.11',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
