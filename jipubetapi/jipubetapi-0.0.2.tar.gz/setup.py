from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = [
    'aiohttp',
    'aiosignal',
    'async-timeout',
    'asyncio',
    'attrs',
    'charset-normalizer',
    'frozenlist',
    'idna',
    'multidict',
    'typing',
    'yarl'
]

setup(
    name="jipubetapi",
    version="0.0.2",
    author="Dmitrii Kazanin",
    author_email="dmitriikazanin@gmail.com",
    description="This library makes it easier to access the API",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/DmitriyUsername/jipubetapi-lib/",
    download_url='https://github.com/DmitriyUsername/jipubetapi-lib/archive/main.zip',
    packages=['jipubetapi'],
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)