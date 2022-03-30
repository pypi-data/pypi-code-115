
import setuptools

setuptools.setup(
    name="smart-pyclics-clustering",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['attrs>=18.2', 'python-louvain', 'networkx==2.1', 'pyclics>=2.0.0'],
)
