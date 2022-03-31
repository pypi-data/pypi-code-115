
import setuptools

setuptools.setup(
    name="smart-hg-20",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['flask==0.11.1', 'celery==5.0.4'],
)
