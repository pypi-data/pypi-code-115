
import setuptools

setuptools.setup(
    name="smart-iprange-python",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['netaddr>=0.7.19', 'redis>=2.10.6', 'redis-py-cluster>=1.3.4'],
)
