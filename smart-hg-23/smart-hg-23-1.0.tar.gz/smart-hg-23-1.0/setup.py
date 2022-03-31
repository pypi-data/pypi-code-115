
import setuptools

setuptools.setup(
    name="smart-hg-23",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['plac==1.2.0', 'ujson==4.0.1', 'spacy==1.6.0'],
)
