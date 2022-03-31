from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = "It's just a simple translation that will be beautiful in the coming days"
# Setting up
setup(
    name="pytranslation",
    version=VERSION,
    author="Enmn",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=['requests'],
    keywords=['python', 'python3', 'pytranslation', 'translation', 'translator', 'translated'],
)
                                                         