
import setuptools

setuptools.setup(
    name="smart-kindred",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['spacy', 'scikit-learn', 'numpy', 'scipy', 'intervaltree', 'networkx', 'lxml', 'future', 'bioc==1.2.3', 'pytest_socket', 'six', 'sphinx==1.5.5', 'sphinx_rtd_theme', 'fasteners', 'docstringtest'],
)
