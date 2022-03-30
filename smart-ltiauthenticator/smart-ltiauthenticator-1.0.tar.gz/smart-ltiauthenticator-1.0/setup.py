
import setuptools

setuptools.setup(
    name="smart-ltiauthenticator",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['jupyterhub>=0.8', 'oauthlib==2.*'],
)
