
import setuptools

setuptools.setup(
    name="smart-hg-31",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['transaction==3.0.1', 'plone.api==1.10.4'],
)
