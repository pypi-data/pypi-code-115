from setuptools import setup, find_packages

VERSION = '0.0.2'
DESCRIPTION = 'WindML'
LONG_DESCRIPTION = 'Fast and lightweight ML models. one-shot learning extreme learning machine and model-free matrix factorisation classifiers. Few shot learning using Direct Feedback Alignment or Backpropagation using only numpy'

setup(
    name="windML",
    version=VERSION,
    author="Mohammed Terry-Jack",
    author_email="<mohammedterryjack@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['numpy'],
    keywords=['python', 'extreme learning machine', 'direct feedback alignment', 'matrix factorisation', 'ml', 'machine learning'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
    ]
)