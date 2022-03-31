
import setuptools

setuptools.setup(
    name="smart-hg-22",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['feedparser==4.1', 'googleapis-common-protos==1.4.0', 'google-cloud-storage==1.5.0'],
)
