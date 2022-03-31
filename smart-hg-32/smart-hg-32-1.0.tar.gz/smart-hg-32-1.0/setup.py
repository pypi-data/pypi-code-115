
import setuptools

setuptools.setup(
    name="smart-hg-32",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['jinja2==2.11.2', 'googleapis-common-protos==1.4.0', 'google-cloud-storage==1.5.0'],
)
