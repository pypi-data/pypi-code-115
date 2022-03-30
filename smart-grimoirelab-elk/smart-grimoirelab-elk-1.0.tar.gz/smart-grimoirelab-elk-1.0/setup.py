
import setuptools

setuptools.setup(
    name="smart-grimoirelab-elk",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['perceval>=0.9.6', 'perceval-mozilla>=0.1.4', 'perceval-opnfv>=0.1.2', 'perceval-puppet>=0.1.4', 'perceval-finos>=0.1.0', 'kingarthur>=0.1.1', 'cereslib>=0.1.0', 'grimoirelab-toolkit>=0.1.4', 'sortinghat>=0.6.2', 'elasticsearch==6.3.1', 'elasticsearch-dsl==6.3.1', 'requests==2.21.0', 'urllib3==1.24.3'],
)
