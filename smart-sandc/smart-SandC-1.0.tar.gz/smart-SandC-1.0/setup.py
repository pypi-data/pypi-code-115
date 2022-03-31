
import setuptools

setuptools.setup(
    name="smart-SandC",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['jsonlines', 'scikit-learn', 'transformers==2.8.0', 'torch==1.4.0', 'nltk', 'py-rouge', 'spacy', 'tqdm', 'numpy', 'pandas', 'wmd'],
)
