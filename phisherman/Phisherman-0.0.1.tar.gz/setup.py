from setuptools import setup

with open("README.md", "r", encoding="utf-8") as handler:
    long_description = handler.read()

setup(
    name = 'Phisherman',
    version = '0.0.1',
    packages = ['phisherman'],
    url = 'https://github.com/IlluminatiFish/Phisherman',
    license = 'Apache 2.0',
    author = 'IlluminatiFish',
    description = 'A simple synchronous API wrapper around Phisherman',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    project_urls = {
        "Bug Tracker": "https://github.com/IlluminatiFish/Phisherman/issues",
    },
    classifiers = [
        "Programming Language :: Python :: 3"
    ],
    install_requires = [
        'requests>=2.23.0',
        'validators>=0.18.2'
    ]
)
