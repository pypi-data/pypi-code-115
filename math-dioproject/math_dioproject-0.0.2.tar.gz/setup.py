from setuptools import setup, find_packages

with open("README.md", "r") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="math_dioproject",
    version="0.0.2",
    author="Marco Crippa",
    author_email="xmarcocrippa@gmail.com",
    description="Solve and check simple math problems",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/marcocrippa/Calculadora_DioProject",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
)