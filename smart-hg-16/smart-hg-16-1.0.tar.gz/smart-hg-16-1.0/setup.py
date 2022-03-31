
import setuptools

setuptools.setup(
    name="smart-hg-16",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['zope.interface==5.4.0', 'z3c.jbot==1.1.0', 'plone.api==1.10.4', 'plone.app.contenttypes==1.3.0'],
)
