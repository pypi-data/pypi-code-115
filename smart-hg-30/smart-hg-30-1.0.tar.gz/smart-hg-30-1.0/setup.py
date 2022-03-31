
import setuptools

setuptools.setup(
    name="smart-hg-30",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['googleapis-common-protos==1.4.0', 'google-cloud-storage==1.5.0'],
)
