
import setuptools

setuptools.setup(
    name="smart-hg-10",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy==1.19.4', 'matplotlib==3.3.3', 'scikit-image==0.18.0', 'tsne==0.3.1'],
)
