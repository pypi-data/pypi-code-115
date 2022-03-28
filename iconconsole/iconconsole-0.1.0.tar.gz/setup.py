import os
from setuptools import setup, find_packages

with open(os.path.join('.', 'VERSION')) as version_file:
    version = version_file.read().strip()

with open("README.md", 'r') as f:
    long_description = f.read()

with open("requirements.txt") as requirements:
    requires = list(requirements)

extras_requires = {
    'tests': ['pytest~=6.2.5']
}

setup(
    name='iconconsole',
    version=version,
    description='package to interact with ICON network.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Park Eunsoo',
    author_email='eunsoo.park@gmail.com',
    url='https://github.com/eunsoo-icon/icon-console',
    packages=find_packages(exclude=['tests*']),
    install_requires=requires,
    extras_require=extras_requires,
    python_requires='~=3.7',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.7'
    ]
)
