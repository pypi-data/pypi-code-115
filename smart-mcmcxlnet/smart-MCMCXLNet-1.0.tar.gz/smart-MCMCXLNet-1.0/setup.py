
import setuptools

setuptools.setup(
    name="smart-MCMCXLNet",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['torch==1.4.0', 'transformers==3.0.2'],
)
