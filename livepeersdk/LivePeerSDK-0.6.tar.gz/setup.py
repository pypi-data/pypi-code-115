import os

from setuptools import setup, find_packages
import setuptools
print("AWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"+os.getcwd())
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='LivePeerSDK',
    version='0.6',
    license='MIT',
    author="Ragavendiran Balasubramanian",
    author_email='bgragavendiran@gmail.com',
    package_dir={'': 'src'},
    url='https://pypi.org/project/LivePeerPython/0.5/',
    project_urls={
        "Git Link": "https://github.com/RAGANITHI/EthernalHacks-LivePeerSDK",
    },
    keywords='LivePeerSDK',
    install_requires=[
        'requests'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description_content_type='text/markdown',
    long_description=long_description,
    python_requires='>=3',

)
