
import setuptools

setuptools.setup(
    name="smart-joint-coref-srl",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['spacy>=2.0.16', 'torch>=0.4.1', 'transformers==3.5'],
)
