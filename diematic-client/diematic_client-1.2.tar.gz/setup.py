# coding=UTF-8
"""Setup for the pipy package"""
import setuptools

with open('README.md', 'r', encoding='utf-8') as long_description_f:
	long_description = long_description_f.read()

setuptools.setup(
  name = 'diematic_client',
  version = '1.2',
  description = 'Asynchronous Python client for diematic-server HTTP server',
	long_description = long_description,
	long_description_content_type = 'text/markdown; charset=UTF-8',
  author = 'Ignacio Hernández-Ros',
  author_email = 'ignacio@hernandez-ros.com',
  packages = ['diematic_client'],
  license='LGPL',
  url = 'https://github.com/IgnacioHR/diematic_client',
  download_url = 'https://github.com/IgnacioHR/diematic_client/archive/refs/tags/v1.2-beta.tar.gz',
  keywords = ['python', 'home-automation', 'iot', 'restful', 'de-dietrich', 'diematic', 'home-assistant'],
  install_requires=[
		'aiohttp',
		'aiosignal',
		'async-timeout',
		'asynctest',
		'attrs',
		'charset-normalizer',
		'deepmerge',
		'frozenlist',
		'idna',
		'multidict',
		'typing-extensions',
		'yarl',
  ],
  classifiers=[
    'Development Status :: 4 - Beta',
		'Environment :: Plugins',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
		'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.7',
		'Topic :: Home Automation',
	],
)