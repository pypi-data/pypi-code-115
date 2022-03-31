
import setuptools

setuptools.setup(
    name="smart-hg-9",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['datetime==4.3', 'products.zcatalog==6.0', 'plone.api==1.10.4'],
)
