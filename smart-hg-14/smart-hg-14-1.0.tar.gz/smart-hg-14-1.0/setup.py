
import setuptools

setuptools.setup(
    name="smart-hg-14",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['zope.interface==5.4.0', 'products.zcatalog==6.0', 'plone.api==1.10.4', 'plone.app.contenttypes==1.3.0'],
)
