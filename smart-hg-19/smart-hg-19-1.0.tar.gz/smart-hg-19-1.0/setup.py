
import setuptools

setuptools.setup(
    name="smart-hg-19",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['django-river==3.3.0', 'django==1.11.29'],
)
