
import setuptools

setuptools.setup(
    name="smart-hg-12",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['products.genericsetup==2.0.3', 'transaction==3.0.1'],
)
