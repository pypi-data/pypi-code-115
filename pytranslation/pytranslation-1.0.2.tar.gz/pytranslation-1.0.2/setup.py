from setuptools import setup, find_packages
import os
import codecs

VERSION = '1.0.2'
DESCRIPTION = "It's just a simple translation that will be beautiful in the coming days"
# Setting up

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os. path.join(here, "README.md"), encoding="utf-8") as file:
    long_description = "\n" + file.read()

setup(
    name="pytranslation",
    version=VERSION,
    author="Enmn",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=['requests'],
    keywords=['python', 'python3', 'pytranslation', 'translation', 'translator', 'translated'],
)
                                                         