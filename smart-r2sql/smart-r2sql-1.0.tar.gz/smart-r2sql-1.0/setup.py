
import setuptools

setuptools.setup(
    name="smart-r2sql",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['torch==1.0.0', 'sqlparse', 'pymysql', 'progressbar', 'nltk', 'numpy', 'six', 'spacy', 'transformers==2.10.0'],
)
